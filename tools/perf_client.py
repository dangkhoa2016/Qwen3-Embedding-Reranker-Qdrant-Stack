from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path


def http_json(base: str, path: str, key: str, *, payload=None):
    headers = {"Authorization": f"Bearer {key}"}
    body = None
    method = "GET"
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(
        base + path, data=body, headers=headers, method=method
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=3600) as response:
            raw = response.read()
            wall_ms = (time.perf_counter() - start) * 1000
            return response.status, json.loads(raw), wall_ms
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        raise RuntimeError(
            f"HTTP {exc.code} {path}: {raw[:1000]!r}"
        ) from exc


def median(values):
    return float(statistics.median(values))


def embedding_case(base, key, text, reps):
    payload = {
        "input": text,
        "input_type": "query",
    }

    # HTTP warm-up; do not include in measured samples.
    status, body, wall = http_json(
        base, "/v1/embeddings", key, payload=payload
    )
    assert status == 200

    samples = []
    for index in range(reps):
        status, body, wall_ms = http_json(
            base, "/v1/embeddings", key, payload=payload
        )
        assert status == 200
        vector = body["data"][0]["embedding"]
        norm = math.sqrt(sum(float(x) * float(x) for x in vector))
        inference_ms = float(body["meta"]["inference_ms"])
        samples.append({
            "rep": index + 1,
            "inference_ms": inference_ms,
            "wall_ms": wall_ms,
            "dimension": len(vector),
            "norm": norm,
        })

    assert all(x["dimension"] == 2560 for x in samples)
    assert all(abs(x["norm"] - 1.0) <= 1e-4 for x in samples)

    return {
        "samples": samples,
        "median_inference_ms": median(
            [x["inference_ms"] for x in samples]
        ),
        "median_wall_ms": median(
            [x["wall_ms"] for x in samples]
        ),
        "dimension": 2560,
        "norm_min": min(x["norm"] for x in samples),
        "norm_max": max(x["norm"] for x in samples),
        "status": "PASS",
    }


def select_docs(corpus, k):
    by_id = {row["id"]: row for row in corpus["candidates"]}
    ids = corpus["k_sets"][str(k)]
    rows = [by_id[item] for item in ids]
    relevant = [i for i, row in enumerate(rows) if row["relevant"]]
    assert len(rows) == k
    assert len(relevant) == 1
    return rows, relevant[0]


def rerank_case(base, key, corpus, k, reps):
    rows, relevant_request_index = select_docs(corpus, k)
    payload = {
        "query": corpus["query"],
        "documents": [row["text"] for row in rows],
        "return_documents": False,
    }

    # One HTTP warm-up for this exact K.
    status, body, wall = http_json(
        base, "/v1/rerank", key, payload=payload
    )
    assert status == 200

    samples = []
    for rep in range(reps):
        status, body, wall_ms = http_json(
            base, "/v1/rerank", key, payload=payload
        )
        assert status == 200
        results = body["results"]
        scores = [float(row["score"]) for row in results]
        assert all(math.isfinite(score) for score in scores)

        rank = None
        thailand_score = None
        for position, result in enumerate(results, start=1):
            if int(result["index"]) == relevant_request_index:
                rank = position
                thailand_score = float(result["score"])
                break

        assert rank is not None
        assert thailand_score is not None
        assert rank == 1

        inference_ms = float(body["meta"]["inference_ms"])
        samples.append({
            "rep": rep + 1,
            "k": k,
            "inference_ms": inference_ms,
            "wall_ms": wall_ms,
            "latency_per_doc_ms": inference_ms / k,
            "docs_per_s": k / (inference_ms / 1000.0),
            "thailand_rank": rank,
            "thailand_score": thailand_score,
            "finite": True,
        })

    return {
        "k": k,
        "samples": samples,
        "median_inference_ms": median(
            [x["inference_ms"] for x in samples]
        ),
        "median_wall_ms": median(
            [x["wall_ms"] for x in samples]
        ),
        "median_latency_per_doc_ms": median(
            [x["latency_per_doc_ms"] for x in samples]
        ),
        "median_docs_per_s": median(
            [x["docs_per_s"] for x in samples]
        ),
        "thailand_rank_all": [x["thailand_rank"] for x in samples],
        "thailand_score_min": min(
            x["thailand_score"] for x in samples
        ),
        "thailand_score_max": max(
            x["thailand_score"] for x in samples
        ),
        "finite_all": all(x["finite"] for x in samples),
        "status": "PASS",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--embedding-reps", type=int, default=3)
    parser.add_argument("--rerank-reps", type=int, default=3)
    parser.add_argument("--k", default="2")
    parser.add_argument("--skip-embedding", action="store_true")
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    key = os.environ["DUAL_API_KEY"]
    corpus_path = Path(args.corpus)
    corpus = json.loads(corpus_path.read_text())
    k_values = [int(x) for x in args.k.split(",") if x.strip()]

    result = {
        "corpus_path": str(corpus_path),
        "corpus_sha256": __import__("hashlib").sha256(
            corpus_path.read_bytes()
        ).hexdigest(),
        "embedding": None,
        "rerank": {},
    }

    if not args.skip_embedding:
        result["embedding"] = embedding_case(
            args.base,
            key,
            corpus["embedding_query"],
            args.embedding_reps,
        )

    for k in k_values:
        result["rerank"][str(k)] = rerank_case(
            args.base, key, corpus, k, args.rerank_reps
        )

    Path(args.out).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()