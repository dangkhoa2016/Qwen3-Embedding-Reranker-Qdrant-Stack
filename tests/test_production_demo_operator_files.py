from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_qdrant_setup_script_is_pinned_to_verified_1_18_3_musl_asset():
    text = (ROOT / "scripts/setup-qdrant-production-demo.sh").read_text()
    assert "QDRANT_VERSION=1.18.3" in text
    assert "qdrant-x86_64-unknown-linux-musl.tar.gz" in text
    assert "b4faedcdf8c9577bf1c8f2ab9b454636b87e056c116c99d49bd4f9fb2e634285" in text
    assert "unknown-linux-gnu" not in text
    assert "--version" in text


def test_snapshot_restore_script_locks_canonical_collection_and_invariants():
    text = (ROOT / "scripts/restore-canonical-qdrant-snapshot.sh").read_text()
    assert "knowledge_entities_qwen3_4b_text_v21" in text
    assert "71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f" in text
    assert "283812352" in text
    assert "points_count" in text
    assert "indexed_vectors_count" in text
    assert "2560" in text
    assert "Cosine" in text
    assert "/kaggle/working" in text
    assert "snapshots/upload?wait=true&priority=snapshot" in text


def test_notebook_is_valid_and_exposes_k5_default_and_stronger_host_example():
    path = ROOT / "notebooks/qwen3_embedding_reranker_qdrant_kaggle_demo.ipynb"
    notebook = json.loads(path.read_text())
    assert notebook["nbformat"] == 4
    sources = "\n".join(
        "".join(cell.get("source", [])) for cell in notebook["cells"]
    )
    assert "RETRIEVAL_TOP_K = 5" in sources
    assert "RERANK_TOP_K = 5" in sources
    assert "DISPLAY_TOP_K = 5" in sources
    assert "RETRIEVAL_TOP_K = 50" in sources
    assert "RERANK_TOP_K = 50" in sources
    assert "LLAMA_SERVER_THREADS = 8" in sources
    assert "RUN_ALL_BUDGET_SECONDS = 600" in sources
    assert "MEMORY_EVENTS_BEFORE" in sources
    assert "oom_delta" in sources
    assert "oom_kill_delta" in sources
    assert "Node.js" not in sources


def test_demo_queries_include_en_vi_and_cross_language_cases():
    cases = json.loads((ROOT / "corpus/production-demo-queries.json").read_text())
    assert {row["category"] for row in cases} == {"en", "vi", "cross-language"}
    assert len(cases) == 3
    assert all(row["expected_names"] for row in cases)
