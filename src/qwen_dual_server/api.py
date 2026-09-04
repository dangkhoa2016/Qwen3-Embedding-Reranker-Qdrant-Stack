from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import __display_name__, __project_name__, __version__
from .config import Settings
from .gate import InferenceGate, QueueFullError
from .schemas import EmbeddingRequest, RerankRequest
from .security import FixedWindowRateLimiter, client_identity, verify_bearer


def create_app(settings: Settings, runtime, *, gate=None) -> FastAPI:
    inference_gate = gate or InferenceGate(
        max_concurrency=settings.max_concurrent_inference,
        max_waiters=settings.max_queue_waiters,
    )
    limiter = FixedWindowRateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.load_models_on_startup:
            await run_in_threadpool(runtime.load_all)
        try:
            yield
        finally:
            close = getattr(runtime, "close", None)
            if close is not None:
                await run_in_threadpool(close)

    app = FastAPI(title=__display_name__, version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.runtime = runtime
    app.state.inference_gate = inference_gate

    @app.middleware("http")
    async def content_length_guard(request: Request, call_next):
        raw = request.headers.get("content-length")
        if raw:
            try:
                length = int(raw)
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "invalid Content-Length"})
            if length > settings.max_request_bytes:
                return JSONResponse(status_code=413, content={"detail": "request body too large"})
        return await call_next(request)

    async def authorized(request: Request):
        verify_bearer(request, settings)
        limiter.check(client_identity(request, settings))

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": __project_name__, "version": __version__}

    @app.get("/ready")
    async def ready():
        is_ready = bool(runtime.status().get("ready"))
        code = 200 if is_ready else 503
        return JSONResponse(
            status_code=code,
            content={"status": "ready" if is_ready else "not_ready", "ready": is_ready},
        )

    @app.get("/v1/models", dependencies=[Depends(authorized)])
    async def models():
        return {"object": "list", "data": runtime.status().get("models", [])}

    @app.get("/v1/stats", dependencies=[Depends(authorized)])
    async def stats():
        body = dict(runtime.stats())
        body["inference_gate"] = inference_gate.snapshot()
        return body

    def validate_instruction(instruction: str | None) -> None:
        if instruction is not None and len(instruction) > settings.max_instruction_chars:
            raise HTTPException(status_code=413, detail="instruction too large")

    @app.post("/v1/embeddings", dependencies=[Depends(authorized)])
    async def embeddings(payload: EmbeddingRequest):
        items = [payload.input] if isinstance(payload.input, str) else payload.input
        if len(items) > settings.max_embedding_items:
            raise HTTPException(status_code=422, detail=f"at most {settings.max_embedding_items} input items are allowed")
        validate_instruction(payload.instruction)
        if sum(len(item) for item in items) > settings.max_text_chars:
            raise HTTPException(status_code=413, detail="embedding input text too large")
        try:
            async with inference_gate.slot() as queue_wait_ms:
                vectors, inference_ms = await run_in_threadpool(
                    runtime.embed, items, payload.input_type, payload.instruction
                )
        except QueueFullError:
            raise HTTPException(status_code=429, detail="inference queue is full")
        rows = vectors.tolist() if hasattr(vectors, "tolist") else vectors
        return {
            "object": "list",
            "model": settings.embedding_model_id,
            "data": [
                {"object": "embedding", "index": i, "embedding": row}
                for i, row in enumerate(rows)
            ],
            "usage": {"input_items": len(items)},
            "meta": {"queue_wait_ms": queue_wait_ms, "inference_ms": round(float(inference_ms), 3)},
        }

    @app.post("/v1/rerank", dependencies=[Depends(authorized)])
    async def rerank(payload: RerankRequest):
        if len(payload.documents) > settings.max_rerank_documents:
            raise HTTPException(status_code=422, detail=f"at most {settings.max_rerank_documents} documents are allowed")
        validate_instruction(payload.instruction)
        if len(payload.query) + sum(len(item) for item in payload.documents) > settings.max_text_chars:
            raise HTTPException(status_code=413, detail="rerank input text too large")
        try:
            async with inference_gate.slot() as queue_wait_ms:
                results, inference_ms = await run_in_threadpool(
                    runtime.rerank, payload.query, payload.documents, payload.instruction
                )
        except QueueFullError:
            raise HTTPException(status_code=429, detail="inference queue is full")
        response_results = []
        for item in results:
            row = {"index": int(item["index"]), "score": float(item["score"])}
            if payload.return_documents:
                row["document"] = payload.documents[row["index"]]
            response_results.append(row)
        return {
            "model": settings.reranker_model_id,
            "results": response_results,
            "meta": {
                "queue_wait_ms": queue_wait_ms,
                "inference_ms": round(float(inference_ms), 3),
                "document_count": len(payload.documents),
            },
        }

    return app
