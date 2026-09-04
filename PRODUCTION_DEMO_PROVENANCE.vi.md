# Provenance source của production demo
> 🌐 Language / Ngôn ngữ: [English](PRODUCTION_DEMO_PROVENANCE.md) | **Tiếng Việt**

## Qualified frozen source

Authoritative Stage-II qualified source là internal artifact:

```text
qwen3-hybrid-fp16-embedding-gguf-reranker-qdrant-production-demo-source-v0.2.3c.zip
size=139820 bytes
SHA256=dfbf98b1e89a123106cea8142e87e1fdcb08175573f361b74024791b7398b8e2
```

`v0.2.3c` là internal qualification label và chưa từng là public release.

Frozen archive không bị sửa tại chỗ. Publication-hygiene work được thực hiện trên các bản extracted/staged.

## Stage-II evidence

Final evidence archive:

```text
qwen3-production-demo-v0.2.3c-stage2-fresh-qualification-evidence.zip
SHA256=0b861e95bb34c2f207e5ad22ea7675891e5711043983a6a5e02b283efd2196a7
ZIP CRC=PASS
MANIFEST=42/42 PASS
```

Final qualification chấp nhận `K=5`, bác bỏ nhu cầu K=2 fallback và đóng R3→R10 corrective chain.

## First public identity

Approved first public package identity là `qwen3-embedding-reranker-qdrant-stack==1.0.0`, author `Đăng Khoa <i.am@dangkhoa.dev>` theo MIT License. Internal import package vẫn là `qwen_dual_server`; historical internal service/lock identifiers được chủ đích giữ lại trong protected qualified configuration.

Temporary local packaging version `0.2.3rc1` chưa từng publish và chỉ được giữ làm provenance.

## Protected semantic contract

Publication work phải giữ byte identity cho:

```text
src/qwen_dual_server/config.py
src/qwen_dual_server/gguf_reranker_engine.py
src/qwen_dual_server/production_demo.py
tests/test_gguf_reranker_engine.py
tests/test_production_demo.py
```

Thay đổi một trong các file này đòi hỏi quyết định xem có phải mở lại Stage-II qualification hay không.
