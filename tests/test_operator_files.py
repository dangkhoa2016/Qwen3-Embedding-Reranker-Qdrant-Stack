from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_start_server_is_single_worker_cpu_safe():
    text = (ROOT / "scripts/start-server.sh").read_text()
    assert "--workers 1" in text
    assert "HF_HUB_OFFLINE" in text
    assert "TRANSFORMERS_OFFLINE" in text
    assert "MAX_CONCURRENT_INFERENCE" in text
    assert "SentenceTransformer" not in text


def test_monitor_records_cgroup_oom_and_peak():
    text = (ROOT / "scripts/start-and-monitor.sh").read_text()
    assert "memory.events" in text
    assert "memory.peak" in text
    assert "oom_kill" in text
    assert "memory-monitor.csv" in text


def test_evidence_collector_does_not_leak_api_key():
    text = (ROOT / "scripts/collect-evidence.sh").read_text()
    assert "DUAL_API_KEY" in text
    assert "REDACTED" in text
    assert "pip-freeze" in text
    assert "memory.events" in text


def test_env_example_freezes_safe_cpu_defaults():
    text = (ROOT / ".env.example").read_text()
    for expected in [
        "MODEL_DTYPE=float16",
        "MAX_SEQ_LENGTH=512",
        "EMBEDDING_MICROBATCH_SIZE=1",
        "RERANKER_MICROBATCH_SIZE=1",
        "MAX_CONCURRENT_INFERENCE=1",
        "SECOND_MODEL_MIN_AVAILABLE_GIB=10",
        "FINAL_MIN_AVAILABLE_GIB=4",
        "ALLOW_REMOTE_MODEL_DOWNLOAD=0",
    ]:
        assert expected in text


def test_dependencies_exclude_sentence_transformers_and_do_not_reinstall_torch():
    text = (ROOT / "requirements.txt").read_text().lower()
    assert "sentence-transformers" not in text
    assert "\ntorch" not in "\n" + text
    assert "transformers" in text
    assert "fastapi" in text
