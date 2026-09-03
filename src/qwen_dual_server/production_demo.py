from __future__ import annotations

import time
import hashlib
from pathlib import Path

import httpx
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DemoConfig:
    retrieval_top_k: int = 5
    rerank_top_k: int = 5
    display_top_k: int = 5
    score_threshold: float | None = None

    def __post_init__(self) -> None:
        values = {
            "retrieval_top_k": self.retrieval_top_k,
            "rerank_top_k": self.rerank_top_k,
            "display_top_k": self.display_top_k,
        }
        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.display_top_k > self.rerank_top_k:
            raise ValueError("display_top_k must be <= rerank_top_k")
        if self.rerank_top_k > self.retrieval_top_k:
            raise ValueError("rerank_top_k must be <= retrieval_top_k")
        if self.rerank_top_k > 200:
            raise ValueError("rerank_top_k must be <= 200")


CANDIDATE_ANSWER_RERANK_INSTRUCTION = """Judge YES only when the Candidate entity itself is the answer entity requested by the Query.
Use the Candidate entity's identity and entity type to decide whether it satisfies what the Query asks for.
Facts in the Document are evidence only. A Document may be relevant and still be NO if its Candidate entity merely contains, names, describes, or points to the correct answer rather than being that answer itself.
Judge NO when the Candidate entity's identity or entity type is incompatible with the requested answer entity."""


class InferenceClient(Protocol):
    def embed_query(self, query: str) -> tuple[list[float], dict[str, Any]]: ...
    def rerank(self, query: str, documents: list[str], instruction: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


class RetrievalClient(Protocol):
    def query(
        self,
        vector: list[float],
        *,
        limit: int,
        score_threshold: float | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _list_text(value: Any) -> str | None:
    if isinstance(value, (list, tuple)):
        items = [_clean(item) for item in value]
        items = [item for item in items if item]
        return ", ".join(items) if items else None
    return _clean(value)


def format_qdrant_payload_for_rerank(payload):
    # Candidate-answer formatter: entity identity first, structured role facts second.
    if not isinstance(payload, dict):
        return str(payload)

    lines = []

    def add(label, value):
        if value is None:
            return
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, (list, tuple, set)):
            text = ", ".join(str(item).strip() for item in value if str(item).strip())
        else:
            text = str(value).strip()
        if text:
            lines.append(f"{label}: {text}.")

    name_en = payload.get("name_en")
    name_vi = payload.get("name_vi")
    primary = name_en or name_vi or payload.get("name") or payload.get("id") or "unknown"

    add("Candidate entity", primary)
    if name_vi and name_vi != primary:
        add("Candidate name (vi)", name_vi)
    if name_en and name_en != primary:
        add("Candidate name (en)", name_en)
    add("Entity type", payload.get("type"))

    facts = payload.get("facts")
    if not isinstance(facts, dict):
        facts = {}

    add("Country", facts.get("country") or payload.get("country"))

    capital = facts.get("capital")
    if isinstance(capital, bool):
        add("Is capital", capital)
    else:
        add("Capital", capital)

    add("Feature code", facts.get("featureCode") or facts.get("feature_code"))
    add("Currency", facts.get("currency"))

    # Compact geographic identity context only. Free-text descriptions are deliberately
    # excluded in this first one-variable corrective.
    add("Region", payload.get("region"))
    add("Continent", payload.get("continent"))
    add("Country code", payload.get("country_code") or payload.get("countryCode"))

    return "\n".join(lines)


def locate_snapshot(
    root: str | Path,
    *,
    filename: str,
    expected_size: int,
    expected_sha256: str,
) -> Path:
    root_path = Path(root)
    matches = [path for path in root_path.rglob(filename) if path.is_file()]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} under {root_path}, found {len(matches)}")
    path = matches[0]
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise ValueError(
            f"snapshot byte size mismatch: expected {expected_size}, got {actual_size}"
        )
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual_sha = digest.hexdigest()
    if actual_sha != expected_sha256.lower():
        raise ValueError(
            f"snapshot SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}"
        )
    return path


class HybridHttpClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: float = 1200.0,
        http: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._owns_http = http is None
        self.http = http or httpx.Client(timeout=timeout_seconds)

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def embed_query(self, query: str) -> tuple[list[float], dict[str, Any]]:
        response = self.http.post(
            f"{self.base_url}/v1/embeddings",
            headers=self.headers,
            json={"input": query, "input_type": "query"},
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or []
        if len(data) != 1 or not isinstance(data[0].get("embedding"), list):
            raise ValueError("invalid embedding response")
        return [float(value) for value in data[0]["embedding"]], dict(body.get("meta") or {})

    def rerank(
        self, query: str, documents: list[str], instruction: str | None = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        payload: dict[str, Any] = {
            "query": query,
            "documents": documents,
            "return_documents": False,
        }
        if instruction is not None:
            payload["instruction"] = instruction
        response = self.http.post(
            f"{self.base_url}/v1/rerank",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()
        body = response.json()
        results = body.get("results")
        if not isinstance(results, list):
            raise ValueError("invalid rerank response")
        normalized = [
            {"index": int(item["index"]), "score": float(item["score"])}
            for item in results
        ]
        return normalized, dict(body.get("meta") or {})

    def close(self) -> None:
        if self._owns_http:
            self.http.close()


class QdrantHttpClient:
    def __init__(
        self,
        base_url: str,
        collection: str,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
        http: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.api_key = api_key
        self._owns_http = http is None
        self.http = http or httpx.Client(timeout=timeout_seconds)

    @property
    def headers(self) -> dict[str, str]:
        return {"api-key": self.api_key} if self.api_key else {}

    @staticmethod
    def _points_from_query_response(body: dict[str, Any]) -> list[dict[str, Any]]:
        result = body.get("result")
        if isinstance(result, dict):
            points = result.get("points")
        else:
            points = result
        if not isinstance(points, list):
            raise ValueError("invalid Qdrant query response")
        return points

    def query(
        self,
        vector: list[float],
        *,
        limit: int,
        score_threshold: float | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        started = time.perf_counter()
        query_body: dict[str, Any] = {
            "query": vector,
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if score_threshold is not None:
            query_body["score_threshold"] = score_threshold
        query_url = f"{self.base_url}/collections/{self.collection}/points/query"
        response = self.http.post(query_url, headers=self.headers, json=query_body)

        if response.status_code == 404:
            legacy_body: dict[str, Any] = {
                "vector": vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
            }
            if score_threshold is not None:
                legacy_body["score_threshold"] = score_threshold
            legacy_url = f"{self.base_url}/collections/{self.collection}/points/search"
            response = self.http.post(legacy_url, headers=self.headers, json=legacy_body)

        response.raise_for_status()
        points = self._points_from_query_response(response.json())
        elapsed = (time.perf_counter() - started) * 1000.0
        return points, {"qdrant_ms": elapsed}

    def close(self) -> None:
        if self._owns_http:
            self.http.close()


class ProductionDemoPipeline:
    def __init__(
        self,
        config: DemoConfig,
        inference_client: InferenceClient,
        qdrant_client: RetrievalClient,
    ) -> None:
        self.config = config
        self.inference_client = inference_client
        self.qdrant_client = qdrant_client

    def search(self, query: str) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        total_started = time.perf_counter()

        vector, embedding_meta = self.inference_client.embed_query(query)
        retrieval, qdrant_meta = self.qdrant_client.query(
            vector,
            limit=self.config.retrieval_top_k,
            score_threshold=self.config.score_threshold,
        )

        rerank_candidates = retrieval[: self.config.rerank_top_k]
        documents = [
            format_qdrant_payload_for_rerank(row.get("payload") or {})
            for row in rerank_candidates
        ]
        if documents:
            rerank_results, rerank_meta = self.inference_client.rerank(query, documents, CANDIDATE_ANSWER_RERANK_INSTRUCTION)
        else:
            rerank_results, rerank_meta = [], {"inference_ms": 0.0}

        ranked: list[dict[str, Any]] = []
        seen: set[int] = set()
        for item in rerank_results:
            index = int(item["index"])
            score = float(item["score"])
            if index < 0 or index >= len(rerank_candidates):
                raise ValueError(f"reranker returned out-of-range index: {index}")
            if index in seen:
                raise ValueError(f"reranker returned duplicate index: {index}")
            seen.add(index)
            ranked.append({**rerank_candidates[index], "rerank_score": score})

        total_ms = (time.perf_counter() - total_started) * 1000.0
        return {
            "query": query,
            "retrieval": retrieval,
            "reranked": ranked,
            "display": ranked[: self.config.display_top_k],
            "meta": {
                "retrieval_top_k": self.config.retrieval_top_k,
                "rerank_top_k": self.config.rerank_top_k,
                "display_top_k": self.config.display_top_k,
                "embedding_ms": float(embedding_meta.get("inference_ms", 0.0)),
                "qdrant_ms": float(qdrant_meta.get("qdrant_ms", 0.0)),
                "rerank_ms": float(rerank_meta.get("inference_ms", 0.0)),
                "total_ms": total_ms,
                "retrieved_count": len(retrieval),
                "reranked_count": len(ranked),
            },
        }
