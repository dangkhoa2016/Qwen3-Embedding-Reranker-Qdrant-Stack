from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable


class LlamaServerError(RuntimeError):
    pass


def resolve_llama_server_binary(explicit: str | Path | None = None) -> Path:
    candidates: list[Path] = []
    if explicit is not None and str(explicit).strip():
        candidates.append(Path(explicit).expanduser())
    else:
        for candidate in (
            Path("/kaggle/working/llama.cpp/build/bin/llama-server"),
            Path("/kaggle/working/llama-server"),
            Path("/opt/llama.cpp/build/bin/llama-server"),
        ):
            candidates.append(candidate)
        found = shutil.which("llama-server")
        if found:
            candidates.append(Path(found))

    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return path

    shown = ", ".join(str(path) for path in candidates) or "none"
    raise LlamaServerError(f"llama-server executable not found; checked: {shown}")


def build_llama_server_argv(
    *,
    binary: Path,
    model_path: Path,
    host: str,
    port: int,
    threads: int,
    context_size: int,
) -> list[str]:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise LlamaServerError("llama-server must bind to loopback for this experiment")
    if port <= 0 or port > 65535:
        raise LlamaServerError(f"invalid llama-server port: {port}")
    if threads < 1:
        raise LlamaServerError("llama-server threads must be >= 1")
    if context_size < 128:
        raise LlamaServerError("llama-server context size must be >= 128")
    if not model_path.is_file():
        raise LlamaServerError(f"GGUF model file does not exist: {model_path}")

    return [
        str(binary),
        "--model", str(model_path),
        "--embedding",
        "--rerank",
        "--pooling", "rank",
        "--host", host,
        "--port", str(port),
        "--threads", str(threads),
        "--ctx-size", str(context_size),
        "--cache-ram", "0",
        "--parallel", "1",
    ]


def _default_health_probe(url: str, timeout: float) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= int(response.status) < 300
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


class LlamaServerProcess:
    def __init__(
        self,
        *,
        binary: Path,
        model_path: Path,
        host: str = "127.0.0.1",
        port: int = 8081,
        threads: int = 2,
        context_size: int = 1024,
        startup_timeout_seconds: float = 180,
        log_path: str | Path = "/tmp/qwen3-reranker-llama-server.log",
        popen_factory: Callable = subprocess.Popen,
        health_probe: Callable[[str, float], bool] = _default_health_probe,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.binary = Path(binary)
        self.model_path = Path(model_path)
        self.host = host
        self.port = int(port)
        self.threads = int(threads)
        self.context_size = int(context_size)
        self.startup_timeout_seconds = float(startup_timeout_seconds)
        self.log_path = Path(log_path)
        self._popen_factory = popen_factory
        self._health_probe = health_probe
        self._sleep = sleep
        self._process = None
        self._log_handle = None

    @property
    def base_url(self) -> str:
        host = "127.0.0.1" if self.host == "localhost" else self.host
        return f"http://{host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}/health"

    @property
    def rerank_url(self) -> str:
        return f"{self.base_url}/v1/rerank"

    @property
    def pid(self) -> int | None:
        return getattr(self._process, "pid", None)

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def argv(self) -> list[str]:
        return build_llama_server_argv(
            binary=self.binary,
            model_path=self.model_path,
            host=self.host,
            port=self.port,
            threads=self.threads,
            context_size=self.context_size,
        )

    def start(self) -> None:
        if self.running:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_handle = self.log_path.open("ab", buffering=0)
        try:
            self._process = self._popen_factory(
                self.argv(),
                stdin=subprocess.DEVNULL,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                shell=False,
                start_new_session=True,
            )
            deadline = time.monotonic() + self.startup_timeout_seconds
            while time.monotonic() < deadline:
                code = self._process.poll()
                if code is not None:
                    raise LlamaServerError(
                        f"llama-server exited during startup with code {code}; log={self.log_path}"
                    )
                if self._health_probe(self.health_url, 2.0):
                    return
                self._sleep(0.25)
            raise LlamaServerError(
                f"llama-server readiness timed out after {self.startup_timeout_seconds:.1f}s; log={self.log_path}"
            )
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
