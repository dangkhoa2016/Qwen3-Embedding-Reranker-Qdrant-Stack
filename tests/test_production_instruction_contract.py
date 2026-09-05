import hashlib

from fastapi.testclient import TestClient

from qwen_dual_server.api import create_app
from qwen_dual_server.config import Settings
from qwen_dual_server.production_demo import CANDIDATE_ANSWER_RERANK_INSTRUCTION

EXPECTED_PRODUCTION_INSTRUCTION = """Judge YES only when the Candidate entity itself is the answer entity requested by the Query.
Use the Candidate entity's identity and entity type to decide whether it satisfies what the Query asks for.
Facts in the Document are evidence only. A Document may be relevant and still be NO if its Candidate entity merely contains, names, describes, or points to the correct answer rather than being that answer itself.
Judge NO when the Candidate entity's identity or entity type is incompatible with the requested answer entity."""
EXPECTED_PRODUCTION_INSTRUCTION_SHA = "81053e1bc7e386372ac6ea12f5523e3ea07c3b35d812f43555b1aa407eda5bc6"


class FakeRuntime:
    def __init__(self):
        self.ready = True
        self.load_error = None
        self.instructions = []

    def load_all(self):
        self.ready = True

    def close(self):
        pass

    def status(self):
        return {
            "ready": self.ready,
            "load_error": self.load_error,
            "models": [
                {"id": "embed", "role": "embedding"},
                {"id": "rerank", "role": "reranker"},
            ],
        }

    def stats(self):
        return {**self.status(), "counters": {}}

    def rerank(self, query, documents, instruction):
        self.instructions.append(instruction)
        return ([{"index": i, "score": 0.9 - i * 0.1} for i in range(len(documents))], 1.0)


def auth():
    return {"Authorization": "Bearer secret"}


def make_app(max_instruction_chars=1024):
    settings = Settings(
        api_key="secret",
        load_models_on_startup=False,
        max_instruction_chars=max_instruction_chars,
    )
    runtime = FakeRuntime()
    return create_app(settings, runtime), runtime


def test_exact_production_instruction_identity_and_default_guardrail():
    assert CANDIDATE_ANSWER_RERANK_INSTRUCTION == EXPECTED_PRODUCTION_INSTRUCTION
    assert len(CANDIDATE_ANSWER_RERANK_INSTRUCTION) == 524
    assert hashlib.sha256(CANDIDATE_ANSWER_RERANK_INSTRUCTION.encode()).hexdigest() == EXPECTED_PRODUCTION_INSTRUCTION_SHA
    settings = Settings(api_key="secret", load_models_on_startup=False)
    assert settings.max_instruction_chars == 1024


def test_api_accepts_exact_production_instruction():
    app, runtime = make_app()
    with TestClient(app) as client:
        r = client.post(
            "/v1/rerank",
            headers=auth(),
            json={
                "query": "q",
                "documents": ["doc-a", "doc-b"],
                "instruction": CANDIDATE_ANSWER_RERANK_INSTRUCTION,
            },
        )
    assert r.status_code == 200, r.text
    assert runtime.instructions == [CANDIDATE_ANSWER_RERANK_INSTRUCTION]


def test_api_accepts_1024_char_instruction():
    app, runtime = make_app()
    instruction = "x" * 1024
    with TestClient(app) as client:
        r = client.post(
            "/v1/rerank",
            headers=auth(),
            json={"query": "q", "documents": ["doc"], "instruction": instruction},
        )
    assert r.status_code == 200, r.text
    assert runtime.instructions == [instruction]


def test_api_rejects_instruction_over_1024():
    app, runtime = make_app()
    with TestClient(app) as client:
        r = client.post(
            "/v1/rerank",
            headers=auth(),
            json={"query": "q", "documents": ["doc"], "instruction": "x" * 1025},
        )
    assert r.status_code == 413, r.text
    assert runtime.instructions == []
