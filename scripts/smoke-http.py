#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import httpx

BASE = os.getenv("SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
KEY = os.getenv("DUAL_API_KEY", "")
OUT = Path(os.getenv("SMOKE_OUTPUT", "/tmp/qwen3-dual-smoke.json"))
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT_SECONDS", "1200"))


def require(cond: bool, message: str):
    if not cond:
        raise AssertionError(message)


def main() -> int:
    evidence = {"base_url": BASE, "checks": []}
    headers = {"Authorization": f"Bearer {KEY}"}
    with httpx.Client(timeout=TIMEOUT) as c:
        r = c.get(f"{BASE}/health"); require(r.status_code == 200, f"health={r.status_code}")
        evidence["checks"].append({"health": r.json()})
        r = c.get(f"{BASE}/ready"); require(r.status_code == 200, f"ready={r.status_code}: {r.text[:300]}")
        evidence["checks"].append({"ready": True})
        r = c.get(f"{BASE}/v1/models"); require(r.status_code == 401, f"unauthorized models should be 401, got {r.status_code}")
        r = c.get(f"{BASE}/v1/models", headers=headers); require(r.status_code == 200, f"models={r.status_code}")
        models = r.json(); require(len(models.get("data", [])) == 2, "expected two loaded models")
        evidence["models"] = models

        r = c.post(f"{BASE}/v1/embeddings", headers=headers, json={"input":"Southeast Asian country whose currency is baht", "input_type":"query"})
        require(r.status_code == 200, f"embedding={r.status_code}: {r.text[:300]}")
        row = r.json()["data"][0]["embedding"]
        norm = math.sqrt(sum(float(x)*float(x) for x in row))
        require(len(row) == 2560, f"embedding dimension={len(row)}")
        require(abs(norm - 1.0) <= 1e-4, f"embedding norm={norm}")
        evidence["embedding"] = {"dimension": len(row), "norm": norm, "meta": r.json().get("meta")}

        docs = [
            "Thailand is a country in Southeast Asia. Its currency is the Thai baht.",
            "Ottawa is the capital city of Canada.",
        ]
        r = c.post(f"{BASE}/v1/rerank", headers=headers, json={"query":"Which Southeast Asian country uses the baht?", "documents":docs, "return_documents":True})
        require(r.status_code == 200, f"rerank={r.status_code}: {r.text[:300]}")
        result = r.json()["results"]
        require(result and result[0]["index"] == 0, f"expected Thailand document rank #1, got {result}")
        evidence["rerank"] = {"results": result, "meta": r.json().get("meta")}

        r = c.get(f"{BASE}/v1/stats", headers=headers); require(r.status_code == 200, f"stats={r.status_code}")
        evidence["stats"] = r.json()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True))
    print(json.dumps({"status":"PASS", "output":str(OUT), "embedding_norm":evidence["embedding"]["norm"], "rerank_top_index":0}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status":"FAIL", "error":f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise
