from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from qwen_dual_server.int8_benchmark import classify_candidate, compute_speedups

root = Path(sys.argv[1])
config = json.loads((root / "evidence" / "candidate-config.json").read_text())
runtime = json.loads((root / "evidence" / "perf-runtime.json").read_text())
bench = json.loads((root / "benchmark" / "benchmark.json").read_text())
stats_after = json.loads((root / "evidence" / "stats-after.json").read_text())


def events(path: Path):
    out = {}
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[0]] = int(parts[1])
    return out

before = events(root / "memory" / "memory.events.before")
after = events(root / "memory" / "memory.events.after")
oom_delta = after.get("oom", 0) - before.get("oom", 0)
kill_delta = after.get("oom_kill", 0) - before.get("oom_kill", 0)
max_delta = after.get("max", 0) - before.get("max", 0)

rows = []
for name in ("startup-monitor.csv", "benchmark-monitor.csv"):
    path = root / "memory" / name
    if path.exists():
        rows.extend(list(csv.DictReader(path.open())))

rss_gib = [int(row["rss_kib"]) / 1024 / 1024 for row in rows if row.get("rss_kib", "").isdigit()]
avail_gib = [int(row["mem_available_kib"]) / 1024 / 1024 for row in rows if row.get("mem_available_kib", "").isdigit()]
current_gib = [int(row["cgroup_current_bytes"]) / 1024**3 for row in rows if row.get("cgroup_current_bytes", "").isdigit()]

embedding = bench.get("embedding")
quality_pass = bool(embedding and embedding.get("status") == "PASS")
for item in bench["rerank"].values():
    quality_pass = quality_pass and item.get("status") == "PASS" and item.get("finite_all") is True
    quality_pass = quality_pass and item.get("thailand_rank_all") == [1] * len(item.get("samples", []))

reranker_ms = {int(k): float(v["median_inference_ms"]) for k, v in bench["rerank"].items()}
speedups = compute_speedups(embedding_ms=float(embedding["median_inference_ms"]), reranker_ms=reranker_ms)
k2_speedup = float(speedups["reranker_speedup_x"].get(2, 0.0))
peak_rss = max(rss_gib) if rss_gib else None
classification = classify_candidate(
    quality_pass=quality_pass,
    k2_speedup_x=k2_speedup,
    oom_delta=oom_delta,
    oom_kill_delta=kill_delta,
    peak_rss_gib=peak_rss,
)
baseline_peak_rss = 19.665172576904297
peak_rss_reduction_pct = ((baseline_peak_rss - peak_rss) / baseline_peak_rss * 100.0 if peak_rss is not None else None)

models = stats_after.get("models", [])
quantized_modules = {
    item.get("role", "unknown"): (item.get("load_report") or {}).get("quantized_weight_modules")
    for item in models
}

summary = {
    "candidate_id": config["candidate_id"],
    "quantization_mode": config["quantization_mode"],
    "threads_configured": config["threads"],
    "threads_effective": runtime["torch_num_threads_effective"],
    "reranker_microbatch": config["reranker_microbatch"],
    "startup_seconds": config["startup_seconds"],
    "embedding": embedding,
    "rerank": bench["rerank"],
    "speedups_vs_frozen_fp16": speedups,
    "quality_pass": quality_pass,
    "promotion_classification": classification,
    "peak_rss_gib_observed": peak_rss,
    "peak_rss_reduction_pct_vs_frozen_fp16": peak_rss_reduction_pct,
    "min_memavailable_gib_observed": min(avail_gib) if avail_gib else None,
    "max_cgroup_current_gib_observed": max(current_gib) if current_gib else None,
    "kernel_cgroup_memory_peak_gib": (stats_after.get("current_memory") or {}).get("cgroup_peak_gib"),
    "cgroup_max_event_delta": max_delta,
    "oom_delta": oom_delta,
    "oom_kill_delta": kill_delta,
    "quantized_weight_modules": quantized_modules,
    "corpus_sha256": bench["corpus_sha256"],
}
(root / "evidence" / "candidate-summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
