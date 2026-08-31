from pathlib import Path

from qwen_dual_server.llama_server import LlamaServerProcess, build_llama_server_argv


def test_build_argv_is_cpu_reranker_loopback(tmp_path: Path):
    model = tmp_path / "Qwen3-Reranker-4B.Q4_K_M.gguf"
    model.write_bytes(b"gguf")
    argv = build_llama_server_argv(
        binary=Path("/opt/llama-server"),
        model_path=model,
        host="127.0.0.1",
        port=8081,
        threads=2,
        context_size=1024,
    )
    assert argv[0] == "/opt/llama-server"
    assert "--model" in argv and str(model) in argv
    assert "--embedding" in argv
    assert "--rerank" in argv
    assert argv[argv.index("--pooling") + 1] == "rank"
    assert argv[argv.index("--host") + 1] == "127.0.0.1"
    assert argv[argv.index("--port") + 1] == "8081"
    assert argv[argv.index("--threads") + 1] == "2"
    assert argv[argv.index("--ctx-size") + 1] == "1024"
    assert argv[argv.index("--cache-ram") + 1] == "0"
    assert argv[argv.index("--parallel") + 1] == "1"
    assert "--n-gpu-layers" not in argv


class FakeProcess:
    def __init__(self):
        self.pid = 4321
        self._poll = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self._poll

    def terminate(self):
        self.terminated = True
        self._poll = 0

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True
        self._poll = -9


def test_process_wrapper_launches_without_shell_and_closes_owned_child(tmp_path: Path):
    calls = []
    fake = FakeProcess()

    def popen(argv, **kwargs):
        calls.append((argv, kwargs))
        return fake

    model = tmp_path / "model.gguf"
    model.write_bytes(b"gguf")
    log = tmp_path / "llama.log"
    server = LlamaServerProcess(
        binary=Path("/opt/llama-server"),
        model_path=model,
        host="127.0.0.1",
        port=8081,
        threads=2,
        context_size=1024,
        startup_timeout_seconds=1,
        log_path=log,
        popen_factory=popen,
        health_probe=lambda url, timeout: True,
        sleep=lambda _: None,
    )
    server.start()
    assert calls
    argv, kwargs = calls[0]
    assert isinstance(argv, list)
    assert kwargs.get("shell") is False
    assert server.pid == 4321
    server.close()
    assert fake.terminated is True
