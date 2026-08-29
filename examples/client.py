#!/usr/bin/env python3
"""Minimal client usable from another Kaggle/Colab notebook."""
import os
import httpx

BASE_URL = os.environ["QWEN_DUAL_URL"].rstrip("/")
API_KEY = os.environ["QWEN_DUAL_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

with httpx.Client(timeout=1200.0) as client:
    emb = client.post(
        f"{BASE_URL}/v1/embeddings",
        headers=HEADERS,
        json={"input": "quốc gia Đông Nam Á sử dụng đồng baht", "input_type": "query"},
    )
    emb.raise_for_status()
    vector = emb.json()["data"][0]["embedding"]
    print("embedding dimension:", len(vector))

    rerank = client.post(
        f"{BASE_URL}/v1/rerank",
        headers=HEADERS,
        json={
            "query": "quốc gia Đông Nam Á sử dụng đồng baht",
            "documents": [
                "Thailand is a country in Southeast Asia. Its currency is the Thai baht.",
                "Vietnam is a country in Southeast Asia. Its currency is the Vietnamese đồng.",
            ],
            "return_documents": True,
        },
    )
    rerank.raise_for_status()
    print(rerank.json())
