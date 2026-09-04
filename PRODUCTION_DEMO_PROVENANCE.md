# Production-demo source provenance

## Qualified frozen source

The authoritative Stage-II qualified source is the internal artifact:

```text
qwen3-hybrid-fp16-embedding-gguf-reranker-qdrant-production-demo-source-v0.2.3c.zip
size=139820 bytes
SHA256=dfbf98b1e89a123106cea8142e87e1fdcb08175573f361b74024791b7398b8e2
```

`v0.2.3c` is an internal qualification label and was never a public release.

The frozen archive was not modified in place. Publication-hygiene work was performed on extracted/staged copies.

## Stage-II evidence

Final evidence archive:

```text
qwen3-production-demo-v0.2.3c-stage2-fresh-qualification-evidence.zip
SHA256=0b861e95bb34c2f207e5ad22ea7675891e5711043983a6a5e02b283efd2196a7
ZIP CRC=PASS
MANIFEST=42/42 PASS
```

The final qualification accepted `K=5`, rejected the need for the K=2 fallback, and closed the R3→R10 corrective chain.

## First public identity

The approved first public package identity is `qwen3-embedding-reranker-qdrant-stack==1.0.0`, authored by `Đăng Khoa <i.am@dangkhoa.dev>` under the MIT License. The internal import package remains `qwen_dual_server`; historical internal service/lock identifiers are intentionally retained in protected qualified configuration.

The temporary local packaging version `0.2.3rc1` was never published and is retained only as provenance.

## Protected semantic contract

Publication work must preserve byte identity for:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

Changing one of these files requires deciding whether Stage-II qualification must be reopened.
