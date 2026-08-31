from __future__ import annotations

BASELINE_FP16 = {
    "source": "frozen Phase E performance qualification evidence",
    "embedding_ms": 7670.984,
    "peak_rss_gib": 19.665172576904297,
    "reranker_ms": {
        2: 61569.442,
        5: 158116.8175,
        10: 315951.01749999996,
        20: 618483.8465,
    },
}


def compute_speedups(*, embedding_ms: float, reranker_ms: dict[int, float]) -> dict[str, object]:
    return {
        "embedding_speedup_x": BASELINE_FP16["embedding_ms"] / float(embedding_ms),
        "reranker_speedup_x": {
            int(k): BASELINE_FP16["reranker_ms"][int(k)] / float(v)
            for k, v in reranker_ms.items()
            if int(k) in BASELINE_FP16["reranker_ms"]
        },
    }


def classify_candidate(
    *,
    quality_pass: bool,
    k2_speedup_x: float,
    oom_delta: int,
    oom_kill_delta: int,
    peak_rss_gib: float | None = None,
    minimum_promote_speedup_x: float = 1.5,
    minimum_peak_rss_reduction_pct: float = 25.0,
) -> str:
    if oom_delta != 0 or oom_kill_delta != 0:
        return "FAIL_MEMORY"
    if not quality_pass:
        return "FAIL_QUALITY"
    if k2_speedup_x < minimum_promote_speedup_x:
        return "DO_NOT_PROMOTE"
    if peak_rss_gib is not None:
        baseline = float(BASELINE_FP16["peak_rss_gib"])
        reduction_pct = (baseline - float(peak_rss_gib)) / baseline * 100.0
        if reduction_pct + 1e-12 < minimum_peak_rss_reduction_pct:
            return "DO_NOT_PROMOTE"
    return "PROMOTE"
