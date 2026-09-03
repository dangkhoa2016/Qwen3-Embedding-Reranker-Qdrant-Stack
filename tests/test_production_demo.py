from __future__ import annotations

import math

import pytest

from qwen_dual_server.production_demo import (
    DemoConfig,
    ProductionDemoPipeline,
    format_qdrant_payload_for_rerank,
)


def test_demo_config_accepts_kaggle_k5_and_stronger_host_k50():
    assert DemoConfig(retrieval_top_k=5, rerank_top_k=5, display_top_k=5).rerank_top_k == 5
    strong = DemoConfig(retrieval_top_k=50, rerank_top_k=50, display_top_k=10)
    assert strong.retrieval_top_k == 50
    assert strong.rerank_top_k == 50
    assert strong.display_top_k == 10


@pytest.mark.parametrize(
    "kwargs",
    [
        {"retrieval_top_k": 2, "rerank_top_k": 5, "display_top_k": 2},
        {"retrieval_top_k": 50, "rerank_top_k": 10, "display_top_k": 20},
        {"retrieval_top_k": 201, "rerank_top_k": 201, "display_top_k": 1},
        {"retrieval_top_k": 0, "rerank_top_k": 0, "display_top_k": 0},
    ],
)
def test_demo_config_rejects_invalid_topk_relationships(kwargs):
    with pytest.raises(ValueError):
        DemoConfig(**kwargs)


def test_format_qdrant_payload_for_rerank_is_deterministic_and_semantic():
    payload = {
        "entity_id": "thailand",
        "type": "country",
        "name_en": "Thailand",
        "name_vi": "Thái Lan",
        "description_en": "country in Southeast Asia",
        "description_vi": "quốc gia ở Đông Nam Á",
        "continent": "Asia",
        "region": "Southeast Asia",
        "country_code": "TH",
        "facts": {
            "capital": "Bangkok",
            "currency": "Baht",
            "languages": ["th", "en"],
        },
        "index_fingerprint": "must-not-leak-into-rerank-document",
    }
    text = format_qdrant_payload_for_rerank(payload)
    assert text == (
        "Candidate entity: Thailand.\n"
        "Candidate name (vi): Thái Lan.\n"
        "Entity type: country.\n"
        "Capital: Bangkok.\n"
        "Currency: Baht.\n"
        "Region: Southeast Asia.\n"
        "Continent: Asia.\n"
        "Country code: TH."
    )
    assert "fingerprint" not in text.lower()


class FakeInferenceClient:
    def embed_query(self, query: str):
        return [1.0, 0.0], {"inference_ms": 12.5}

    def rerank(self, query: str, documents: list[str], instruction: str | None = None):
        assert len(documents) == 3
        return [
            {"index": 2, "score": 0.91},
            {"index": 0, "score": 0.55},
            {"index": 1, "score": 0.11},
        ], {"inference_ms": 33.0}


class FakeQdrantClient:
    def query(self, vector: list[float], *, limit: int, score_threshold: float | None):
        assert vector == [1.0, 0.0]
        assert limit == 5
        return [
            {"id": "a", "score": 0.80, "payload": {"name_en": "Alpha", "type": "city"}},
            {"id": "b", "score": 0.79, "payload": {"name_en": "Beta", "type": "city"}},
            {"id": "c", "score": 0.78, "payload": {"name_en": "Gamma", "type": "city"}},
            {"id": "d", "score": 0.77, "payload": {"name_en": "Delta", "type": "city"}},
            {"id": "e", "score": 0.76, "payload": {"name_en": "Epsilon", "type": "city"}},
        ], {"qdrant_ms": 3.0}


def test_pipeline_retrieves_five_reranks_three_and_displays_two():
    config = DemoConfig(retrieval_top_k=5, rerank_top_k=3, display_top_k=2)
    pipeline = ProductionDemoPipeline(config, FakeInferenceClient(), FakeQdrantClient())
    result = pipeline.search("query")

    assert [row["id"] for row in result["retrieval"]] == ["a", "b", "c", "d", "e"]
    assert [row["id"] for row in result["reranked"]] == ["c", "a", "b"]
    assert [row["id"] for row in result["display"]] == ["c", "a"]
    assert result["reranked"][0]["rerank_score"] == pytest.approx(0.91)
    assert result["meta"]["retrieval_top_k"] == 5
    assert result["meta"]["rerank_top_k"] == 3
    assert result["meta"]["display_top_k"] == 2
    assert result["meta"]["embedding_ms"] == pytest.approx(12.5)
    assert result["meta"]["qdrant_ms"] == pytest.approx(3.0)
    assert result["meta"]["rerank_ms"] == pytest.approx(33.0)
    assert math.isfinite(result["meta"]["total_ms"])


def test_hybrid_http_client_uses_existing_api_contract():
    import httpx
    from qwen_dual_server.production_demo import HybridHttpClient

    requests = []

    def handler(request: httpx.Request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer secret"
        if request.url.path == "/v1/embeddings":
            body = __import__("json").loads(request.content)
            assert body == {"input": "hello", "input_type": "query"}
            return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}], "meta": {"inference_ms": 7.5}})
        if request.url.path == "/v1/rerank":
            body = __import__("json").loads(request.content)
            assert body == {"query": "hello", "documents": ["a", "b"], "return_documents": False}
            return httpx.Response(200, json={"results": [{"index": 1, "score": 0.9}, {"index": 0, "score": 0.1}], "meta": {"inference_ms": 11.0}})
        raise AssertionError(request.url.path)

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://hybrid")
    client = HybridHttpClient("http://hybrid", "secret", http=http)
    vector, emb_meta = client.embed_query("hello")
    ranking, rerank_meta = client.rerank("hello", ["a", "b"])
    assert vector == [0.1, 0.2]
    assert emb_meta["inference_ms"] == 7.5
    assert ranking[0] == {"index": 1, "score": 0.9}
    assert rerank_meta["inference_ms"] == 11.0
    assert [r.url.path for r in requests] == ["/v1/embeddings", "/v1/rerank"]


def test_qdrant_http_client_parses_query_api_points():
    import httpx
    from qwen_dual_server.production_demo import QdrantHttpClient

    def handler(request: httpx.Request):
        assert request.url.path == "/collections/demo/points/query"
        body = __import__("json").loads(request.content)
        assert body["query"] == [0.1, 0.2]
        assert body["limit"] == 5
        assert body["with_payload"] is True
        return httpx.Response(200, json={"result": {"points": [{"id": "x", "score": 0.8, "payload": {"name_en": "X"}}]}})

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://qdrant")
    client = QdrantHttpClient("http://qdrant", "demo", http=http)
    points, meta = client.query([0.1, 0.2], limit=5, score_threshold=None)
    assert points == [{"id": "x", "score": 0.8, "payload": {"name_en": "X"}}]
    assert meta["qdrant_ms"] >= 0


def test_qdrant_http_client_falls_back_to_legacy_search_on_404():
    import httpx
    from qwen_dual_server.production_demo import QdrantHttpClient

    paths = []

    def handler(request: httpx.Request):
        paths.append(request.url.path)
        if request.url.path.endswith("/points/query"):
            return httpx.Response(404, json={"status": {"error": "not found"}})
        if request.url.path.endswith("/points/search"):
            body = __import__("json").loads(request.content)
            assert body["vector"] == [1.0, 0.0]
            assert body["score_threshold"] == 0.55
            return httpx.Response(200, json={"result": [{"id": "y", "score": 0.9, "payload": {"name_en": "Y"}}]})
        raise AssertionError(request.url.path)

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://qdrant")
    client = QdrantHttpClient("http://qdrant", "demo", http=http)
    points, _ = client.query([1.0, 0.0], limit=5, score_threshold=0.55)
    assert points[0]["id"] == "y"
    assert paths == ["/collections/demo/points/query", "/collections/demo/points/search"]


def test_locate_snapshot_requires_exact_name_size_and_sha(tmp_path):
    import hashlib
    from qwen_dual_server.production_demo import locate_snapshot

    nested = tmp_path / "dataset" / "version" / "1"
    nested.mkdir(parents=True)
    payload = b"canonical-test-snapshot"
    target = nested / "canonical.snapshot"
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    found = locate_snapshot(
        tmp_path,
        filename="canonical.snapshot",
        expected_size=len(payload),
        expected_sha256=digest,
    )
    assert found == target

    with pytest.raises(ValueError, match="SHA-256"):
        locate_snapshot(
            tmp_path,
            filename="canonical.snapshot",
            expected_size=len(payload),
            expected_sha256="0" * 64,
        )


def test_locate_snapshot_rejects_ambiguous_matches(tmp_path):
    import hashlib
    from qwen_dual_server.production_demo import locate_snapshot

    payload = b"same"
    digest = hashlib.sha256(payload).hexdigest()
    for folder in ("a", "b"):
        d = tmp_path / folder
        d.mkdir()
        (d / "canonical.snapshot").write_bytes(payload)

    with pytest.raises(ValueError, match="exactly one"):
        locate_snapshot(
            tmp_path,
            filename="canonical.snapshot",
            expected_size=len(payload),
            expected_sha256=digest,
        )
