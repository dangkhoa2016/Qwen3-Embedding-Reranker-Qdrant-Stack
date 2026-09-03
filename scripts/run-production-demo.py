#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from qwen_dual_server.production_demo import DemoConfig, HybridHttpClient, ProductionDemoPipeline, QdrantHttpClient

ROOT = Path(__file__).resolve().parents[1]
queries = json.loads((ROOT / "corpus/production-demo-queries.json").read_text())
config = DemoConfig(
    retrieval_top_k=int(os.environ.get("RETRIEVAL_TOP_K", "5")),
    rerank_top_k=int(os.environ.get("RERANK_TOP_K", "5")),
    display_top_k=int(os.environ.get("DISPLAY_TOP_K", "5")),
    score_threshold=(float(os.environ["QDRANT_SCORE_THRESHOLD"]) if os.environ.get("QDRANT_SCORE_THRESHOLD") else None),
)
api_key = os.environ.get("DUAL_API_KEY", "")
if not api_key:
    raise SystemExit("DUAL_API_KEY is required")
inference = HybridHttpClient(os.environ.get("HYBRID_URL", "http://127.0.0.1:8000"), api_key)
qdrant = QdrantHttpClient(
    os.environ.get("QDRANT_URL", "http://127.0.0.1:6333"),
    os.environ.get("QDRANT_COLLECTION", "knowledge_entities_qwen3_4b_text_v21"),
)
pipeline = ProductionDemoPipeline(config, inference, qdrant)

results = []
try:
    for case in queries:
        result = pipeline.search(case["query"])
        expected = {name.casefold() for name in case["expected_names"]}
        top = result["reranked"][0]["payload"] if result["reranked"] else {}
        observed = {str(top.get("name_en", "")).casefold(), str(top.get("name_vi", "")).casefold()}
        result["case_id"] = case["id"]
        result["category"] = case["category"]
        result["expected_names"] = case["expected_names"]
        result["expected_top1_pass"] = bool(expected & observed)
        results.append(result)
finally:
    inference.close()
    qdrant.close()

summary = {
    "profile": {"retrieval_top_k": config.retrieval_top_k, "rerank_top_k": config.rerank_top_k, "display_top_k": config.display_top_k},
    "all_expected_top1_pass": all(row["expected_top1_pass"] for row in results),
    "cases": results,
}
json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
print()
