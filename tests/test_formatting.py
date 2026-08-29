from qwen_dual_server.formatting import (
    CANONICAL_EMBEDDING_INSTRUCTION,
    DEFAULT_RERANK_INSTRUCTION,
    RERANK_PREFIX,
    RERANK_SUFFIX,
    format_embedding_text,
    format_reranker_pair,
)


def test_canonical_query_format_is_snapshot_compatible():
    assert format_embedding_text("Thái Lan", "query", None) == (
        "Instruct: Retrieve the geographic entity that best answers the query\n"
        "Query:Thái Lan"
    )
    assert CANONICAL_EMBEDDING_INSTRUCTION == "Retrieve the geographic entity that best answers the query"


def test_document_embedding_text_is_raw():
    text = "Thailand. Thái Lan. Country in Southeast Asia."
    assert format_embedding_text(text, "document", "ignored") == text


def test_custom_query_instruction_is_supported():
    assert format_embedding_text("hello", "query", "Find matching software docs") == (
        "Instruct: Find matching software docs\nQuery:hello"
    )


def test_reranker_pair_matches_qwen_protocol():
    body = format_reranker_pair("capital?", "Bangkok is the capital of Thailand", None)
    assert body == (
        f"<Instruct>: {DEFAULT_RERANK_INSTRUCTION}\n"
        "<Query>: capital?\n"
        "<Document>: Bangkok is the capital of Thailand"
    )
    assert 'answer can only be "yes" or "no"' in RERANK_PREFIX
    assert RERANK_SUFFIX.endswith("<think>\n\n</think>\n\n")
