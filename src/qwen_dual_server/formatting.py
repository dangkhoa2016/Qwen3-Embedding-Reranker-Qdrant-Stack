from typing import Literal

CANONICAL_EMBEDDING_INSTRUCTION = "Retrieve the geographic entity that best answers the query"
DEFAULT_RERANK_INSTRUCTION = "Given a web search query, retrieve relevant passages that answer the query"

RERANK_PREFIX = (
    '<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the '
    'Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n'
    '<|im_start|>user\n'
)
RERANK_SUFFIX = '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'


def format_embedding_text(
    text: str,
    input_type: Literal["query", "document"],
    instruction: str | None,
) -> str:
    if input_type == "document":
        return text
    chosen = instruction or CANONICAL_EMBEDDING_INSTRUCTION
    return f"Instruct: {chosen}\nQuery:{text}"


def format_reranker_pair(query: str, document: str, instruction: str | None) -> str:
    chosen = instruction or DEFAULT_RERANK_INSTRUCTION
    return f"<Instruct>: {chosen}\n<Query>: {query}\n<Document>: {document}"
