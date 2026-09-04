# v0.1.1 Release Notes
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v0.1.1.vi.md)

**Date:** 2026-08-30
**Type:** Corrective release

v0.1.0 remains the empirically qualified baseline.
v0.1.1 is corrective, not a performance promotion.

## What is explicitly NOT in this release

- No runtime safety defaults were increased.
- No Node/Qdrant integration is included.
- No BF16/microbatch/thread/top-K result is claimed yet.
- No new model, quantization, GGUF, prompt, or scoring change.

## Corrective changes in v0.1.1

1. **Fail-closed secret scan without self-output collision.**
   The operator runbook's final evidence secret scan now captures grep output
   to a temporary file outside the scanned tree, excludes its own result file,
   and distinguishes PASS (RC=1), secret found (RC=0, hard FAIL), and scan
   execution error (any other RC, hard FAIL).

2. **Authoritative sidecar requirement / provenance wording.**
   Source-integrity verification now requires the supplied authoritative
   `.sha256` sidecar as formal provenance input. A locally generated digest is
   labeled informational only; a missing sidecar marks provenance
   `BLOCKED_AUTHORITATIVE_SIDECAR_MISSING` and the run halts.

3. **Modern Transformers dtype keyword on supported runtime, with
   compatibility handling.**
   Model loading no longer passes the deprecated `torch_dtype` keyword on
   Transformers runtimes that support `dtype`. A capability-based selector
   picks `dtype` when the installed `PreTrainedModel.from_pretrained` supports
   it and falls back to legacy `torch_dtype` only when required.

4. **Redundant tokenizer pad `max_length` warning removed.**
   The reranker's final dynamic `tokenizer.pad(...)` call no longer passes an
   ignored `max_length=`, removing the
   "`max_length` is ignored when `padding`=`True` and there is no truncation
   strategy" warning while preserving the exact bounded output.

5. **Explicit embedding/reranker <=512-token regressions.**
   Added fake-tokenizer regression tests that send inputs far beyond 512 tokens
   and assert the tensors actually passed to both models are bounded to
   512, the embedding trailing pooling special token is retained, the Qwen
   reranker prompt/scoring structure is unchanged, and the dynamic pad call
   stays warning-clean.

## Qualified runtime defaults (unchanged)

```text
MODEL_DTYPE                  = float16
MAX_SEQ_LENGTH               = 512
EMBEDDING_MICROBATCH_SIZE    = 1
RERANKER_MICROBATCH_SIZE     = 1
MAX_CONCURRENT_INFERENCE     = 1
Uvicorn workers              = 1
Embedding model instances    = 1
Reranker model instances     = 1
SECOND_MODEL_MIN_AVAILABLE_GIB = 10
FINAL_MIN_AVAILABLE_GIB      = 4
public embedding dtype       = float32
embedding dimension          = 2560
remote model downloads       = disabled
server bind                  = 127.0.0.1
Bearer authentication        = enabled for model endpoints
```

## Performance — next phase

No performance result is claimed here. The next phase is a separate
performance-qualification campaign that must preserve `v0.1.0` as the control
and change one variable at a time:

```text
FP16 control
-> BF16 candidate
-> thread count 2/4
-> reranker microbatch 1/2/4
-> measured K=2/5/10/20
-> only then Node/Qdrant integration decision
```

Node/Qdrant integration is NOT started by this corrective release.
