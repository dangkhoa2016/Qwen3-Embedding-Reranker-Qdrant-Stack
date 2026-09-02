from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .gguf_locator import DEFAULT_RERANKER_GGUF_BASENAME, resolve_reranker_gguf
from .llama_server import LlamaServerProcess, resolve_llama_server_binary


def _default_http_post(url: str, body: dict[str, object], timeout: float) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if int(response.status) != 200:
                raise RuntimeError(f"llama-server rerank returned HTTP {response.status}")
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"llama-server rerank HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"llama-server rerank request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("llama-server rerank response must be a JSON object")
    return payload


def _quantization_from_name(path: Path) -> str:
    name = path.name
    prefix = "Qwen3-Reranker-4B."
    suffix = ".gguf"
    if name.startswith(prefix) and name.endswith(suffix):
        return name[len(prefix):-len(suffix)]
    return "unknown"


class UnsupportedInstructionError(RuntimeError):
    """Raised when a custom rerank instruction is requested but the backend cannot prove it applies."""


class GGUFRerankerEngine:
    def __init__(
        self,
        settings,
        *,
        server_factory: Callable = LlamaServerProcess,
        binary_resolver: Callable[[str | None], Path] = resolve_llama_server_binary,
        http_post: Callable[[str, dict[str, object], float], dict[str, object]] = _default_http_post,
        functional_probe: bool = True,
    ):
        self.settings = settings
        self._server_factory = server_factory
        self._binary_resolver = binary_resolver
        self._http_post = http_post
        self._functional_probe = functional_probe
        self.model_path: Path | None = None
        self.server = None
        self._loaded = False
        self._supports_custom_instruction: bool = False
        self._instruction_probe_detail: str = "not probed"

    @staticmethod
    def _probe_instruction_changes_score(call_a, call_b) -> bool:
        """Compare two backend calls (instruction omitted vs present)."""
        try:
            pa, pb = call_a(), call_b()
        except Exception:
            return False
        results_a = pa.get("results", []) if isinstance(pa, dict) else []
        results_b = pb.get("results", []) if isinstance(pb, dict) else []
        scores_a = [float(r["relevance_score"]) for r in results_a]
        scores_b = [float(r["relevance_score"]) for r in results_b]
        finite = all(math.isfinite(v) for v in scores_a + scores_b)
        same_card = len(scores_a) == len(scores_b) > 0
        if not (finite and same_card):
            return False
        eps = 1e-4
        return any(math.fabs(a - b) > eps for a, b in zip(scores_a, scores_b))

    def load(self) -> None:
        if self._loaded:
            return
        model_path = resolve_reranker_gguf(
            getattr(self.settings, "reranker_gguf_path", None),
            getattr(self.settings, "kaggle_input_root", "/kaggle/input"),
            DEFAULT_RERANKER_GGUF_BASENAME,
        )
        binary = self._binary_resolver(getattr(self.settings, "llama_server_bin", None))
        log_path = Path(getattr(self.settings, "llama_server_log_path", "/tmp/qwen3-reranker-llama-server.log"))
        server = self._server_factory(
            binary=binary,
            model_path=model_path,
            host=getattr(self.settings, "llama_server_host", "127.0.0.1"),
            port=int(getattr(self.settings, "llama_server_port", 8081)),
            threads=int(getattr(self.settings, "llama_server_threads", 2)),
            context_size=int(getattr(self.settings, "llama_server_context_size", 1024)),
            startup_timeout_seconds=float(
                getattr(self.settings, "llama_server_startup_timeout_seconds", 180)
            ),
            log_path=log_path,
        )
        try:
            server.start()
            self.model_path = model_path
            self.server = server
            self._loaded = True
            if self._functional_probe:
                probe = self.rerank(
                    "Which document is about Thailand?",
                    [
                        "Thailand is a country in Southeast Asia whose capital is Bangkok.",
                        "The Moon is Earth's natural satellite.",
                    ],
                    None,
                )
                if len(probe) != 2:
                    raise RuntimeError("GGUF reranker functional probe did not return two results")
                if int(probe[0]["index"]) != 0:
                    raise RuntimeError("GGUF reranker functional probe failed: Thailand document was not rank #1")
                changed = self._probe_instruction_changes_score(
                    lambda: self._http_post(
                        self.server.rerank_url,
                        {
                            "query": "Which document is about Thailand?",
                            "documents": [
                                "Thailand is a country in Southeast Asia whose capital is Bangkok.",
                                "The Moon is Earth's natural satellite.",
                            ],
                            "top_n": 2,
                        },
                        3600.0,
                    ),
                    lambda: self._http_post(
                        self.server.rerank_url,
                        {
                            "query": "Which document is about Thailand?",
                            "documents": [
                                "Thailand is a country in Southeast Asia whose capital is Bangkok.",
                                "The Moon is Earth's natural satellite.",
                            ],
                            "top_n": 2,
                            "instruction": "Given a web search query, retrieve relevant passages that answer the query.",
                        },
                        3600.0,
                    ),
                )
                self._supports_custom_instruction = changed
                self._instruction_probe_detail = (
                    "custom_instruction_changes_backend_score" if changed
                    else "custom_instruction_scored_identical_to_baseline"
                )
                if not changed:
                    print("[gguf-reranker-engine] WARNING: custom instruction probe returned identical scores; "
                          "supports_custom_instruction disabled (fail-closed)")
        except Exception:
            self._loaded = False
            self.server = None
            self.model_path = None
            server.close()
            raise

    def _parse_results(self, payload: dict[str, object], document_count: int) -> list[dict[str, object]]:
        raw_results = payload.get("results")
        if not isinstance(raw_results, list) or len(raw_results) != document_count:
            raise RuntimeError(
                "llama-server rerank must return exactly one result per input document"
            )

        seen: set[int] = set()
        parsed: list[dict[str, object]] = []
        for item in raw_results:
            if not isinstance(item, dict):
                raise RuntimeError("llama-server rerank result must be an object")
            try:
                index = int(item["index"])
                score = float(item["relevance_score"])
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError("llama-server rerank result is missing index/relevance_score") from exc
            if index < 0 or index >= document_count:
                raise RuntimeError(f"llama-server rerank index out of range: {index}")
            if index in seen:
                raise RuntimeError(f"llama-server rerank duplicate index: {index}")
            if not math.isfinite(score):
                raise RuntimeError("llama-server rerank relevance_score must be finite")
            seen.add(index)
            parsed.append({"index": index, "score": score})

        if seen != set(range(document_count)):
            raise RuntimeError("llama-server rerank result indices do not cover all documents")
        parsed.sort(key=lambda row: float(row["score"]), reverse=True)
        return parsed

    def rerank(
        self,
        query: str,
        documents: list[str],
        instruction: str | None,
    ) -> list[dict[str, object]]:
        if not self._loaded or self.server is None:
            raise RuntimeError("GGUF reranker is not loaded")
        if not documents:
            return []
        return self._backend_rerank(query, documents, instruction)

    def _backend_rerank(
        self,
        query: str,
        documents: list[str],
        instruction: str | None,
    ) -> list[dict[str, object]]:
        payload: dict[str, object] = {
            "query": query,
            "documents": list(documents),
            "top_n": len(documents),
        }
        if instruction is not None:
            if not self._supports_custom_instruction:
                raise UnsupportedInstructionError(
                    "backend capability probe could not prove custom instruction changes rerank scores; "
                    "custom instruction is disabled (fail-closed)"
                )
            payload["instruction"] = instruction
        response = self._http_post(self.server.rerank_url, payload, 3600.0)
        return self._parse_results(response, len(documents))

    def warmup(self) -> None:
        if not self._loaded:
            raise RuntimeError("GGUF reranker is not loaded")
        self.rerank(
            "Thailand",
            ["Thailand is in Southeast Asia.", "A violin is a musical instrument."],
            None,
        )

    def metadata(self) -> dict[str, object]:
        path = self.model_path
        return {
            "id": self.settings.reranker_model_id,
            "role": "reranker",
            "path": str(path) if path is not None else str(getattr(self.settings, "reranker_gguf_path", "") or ""),
            "backend": "llama_cpp",
            "runtime": "llama.cpp-cpu",
            "device": "cpu",
            "dtype": "gguf-quantized",
            "quantization_mode": "none",
            "format": "gguf",
            "quantization": _quantization_from_name(path) if path is not None else "Q4_K_M",
            "max_seq_length": getattr(self.settings, "max_seq_length", 512),
            "microbatch_size": getattr(self.settings, "reranker_microbatch_size", 1),
            "loaded": self._loaded,
            "backend_pid": getattr(self.server, "pid", None) if self.server is not None else None,
            "backend_base_url": getattr(self.server, "base_url", None) if self.server is not None else None,
            "supports_custom_instruction": self._supports_custom_instruction,
            "custom_instruction_probe": self._instruction_probe_detail,
            "load_report": {
                "backend": "llama_cpp",
                "format": "gguf",
                "quantization": _quantization_from_name(path) if path is not None else "Q4_K_M",
            } if self._loaded else None,
        }

    def close(self) -> None:
        server = self.server
        self.server = None
        self._loaded = False
        if server is not None:
            server.close()
