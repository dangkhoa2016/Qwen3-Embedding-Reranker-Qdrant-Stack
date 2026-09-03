# Production-demo source provenance

Target parent artifact: `qwen3-hybrid-fp16-embedding-gguf-reranker-full-source-v0.1.0.zip`, SHA-256 `aa4608c1bc8764246dc0cdeb5d932564d72a4ae7ea9f1ba5ee18e104df7fef81`.

The current tool runtime did not expose that uploaded binary as a mountable `/mnt/data` file. To avoid fabricating a claim of byte-for-byte modification, this working tree was reconstructed from the locally available baseline source archive plus the already-qualified GGUF hybrid overlay, then extended only with the production-demo/Qdrant layer and its tests/operator files.

Therefore the output package is a **new derived source artifact**, not a claim that the original ZIP was modified in place byte-for-byte. Core embedding/GGUF inference files are intentionally left unchanged by the production-demo feature work.
