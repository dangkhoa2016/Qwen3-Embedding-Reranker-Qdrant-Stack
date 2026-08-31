from qwen_dual_server.int8_benchmark import BASELINE_FP16, classify_candidate, compute_speedups


def test_frozen_baseline_matches_phase_e_evidence():
    assert BASELINE_FP16["embedding_ms"] == 7670.984
    assert BASELINE_FP16["reranker_ms"][2] == 61569.442
    assert BASELINE_FP16["reranker_ms"][5] == 158116.8175
    assert BASELINE_FP16["reranker_ms"][10] == 315951.01749999996


def test_compute_speedups_uses_lower_latency_as_faster():
    result = compute_speedups(
        embedding_ms=3835.492,
        reranker_ms={2: 30784.721, 5: 79058.40875, 10: 157975.50875},
    )
    assert abs(result["embedding_speedup_x"] - 2.0) < 1e-9
    assert abs(result["reranker_speedup_x"][2] - 2.0) < 1e-9


def test_candidate_promotes_only_with_quality_and_at_least_1_5x_k2():
    assert classify_candidate(quality_pass=True, k2_speedup_x=1.5, oom_delta=0, oom_kill_delta=0) == "PROMOTE"
    assert classify_candidate(quality_pass=True, k2_speedup_x=1.49, oom_delta=0, oom_kill_delta=0) == "DO_NOT_PROMOTE"
    assert classify_candidate(quality_pass=False, k2_speedup_x=3.0, oom_delta=0, oom_kill_delta=0) == "FAIL_QUALITY"
    assert classify_candidate(quality_pass=True, k2_speedup_x=3.0, oom_delta=1, oom_kill_delta=0) == "FAIL_MEMORY"


def test_candidate_requires_25_percent_peak_rss_reduction_for_promotion():
    from qwen_dual_server.int8_benchmark import BASELINE_FP16
    baseline = BASELINE_FP16["peak_rss_gib"]
    assert classify_candidate(
        quality_pass=True, k2_speedup_x=2.0, oom_delta=0, oom_kill_delta=0,
        peak_rss_gib=baseline * 0.75,
    ) == "PROMOTE"
    assert classify_candidate(
        quality_pass=True, k2_speedup_x=2.0, oom_delta=0, oom_kill_delta=0,
        peak_rss_gib=baseline * 0.80,
    ) == "DO_NOT_PROMOTE"
