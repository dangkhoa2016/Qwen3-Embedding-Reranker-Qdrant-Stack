from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.md"


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


def test_secret_scan_uses_external_temp_output_then_copies_result():
    text = RUNBOOK.read_text(encoding="utf-8")

    assert 'TMP_SCAN="$(mktemp)"' in text
    assert "--exclude='secret-scan.txt'" in text
    assert '> "$TMP_SCAN"' in text
    assert "SECRET_RC=$?" in text

    # RC=1 => no match => PASS
    assert 'if [ "$SECRET_RC" -eq 1 ]' in text

    # RC=0 => actual secret found => FAIL
    assert 'elif [ "$SECRET_RC" -eq 0 ]' in text

    # Other return code => scan execution failure
    assert "secret scan execution error" in text

    # The corrected scan must capture grep output outside RUN_ROOT first.
    assert (
        'grep -R --line-number --fixed-string "$DUAL_API_KEY" "$RUN_ROOT"'
        in text
    )
    assert '> "$TMP_SCAN"' in text

    # The old direct grep-output target must not return.
    old_direct_target = (
        'grep -R --line-number --fixed-string "$DUAL_API_KEY" "$RUN_ROOT" \\\n'
        "  --exclude='*.zip' --exclude='*.sha256' \\\n"
        '  > "$RUN_ROOT/evidence/secret-scan.txt"'
    )
    assert old_direct_target not in text


def test_source_integrity_requires_authoritative_sidecar():
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "BLOCKED_AUTHORITATIVE_SIDECAR_MISSING" in text
    assert "informational" in text.lower()
    assert "independent" in text.lower()

    # Do not fabricate a new expected sidecar from the archive
    # and then compare the archive against itself.
    assert 'sha256sum "$SOURCE_ZIP" > "$SOURCE_SHA"' not in text
