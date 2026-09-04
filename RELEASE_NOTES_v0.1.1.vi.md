# Release Notes v0.1.1
> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v0.1.1.md) | **Tiếng Việt**

**Ngày:** 2026-08-30  
**Loại:** Corrective release

v0.1.0 vẫn là empirically qualified baseline.  
v0.1.1 là corrective, không phải performance promotion.

## Những gì rõ ràng KHÔNG có trong release này

- Không tăng runtime safety defaults.
- Không có Node/Qdrant integration.
- Chưa claim kết quả BF16/microbatch/thread/top-K nào.
- Không có model, quantization, GGUF, prompt hoặc scoring change mới.

## Corrective changes trong v0.1.1

1. **Fail-closed secret scan không tự va chạm với output của chính nó.**  
   Final evidence secret scan trong operator runbook ghi grep output vào temporary file nằm ngoài scanned tree, loại trừ own result file và phân biệt PASS (RC=1), tìm thấy secret (RC=0, hard FAIL) và lỗi thực thi scan (RC khác, hard FAIL).

2. **Authoritative sidecar requirement / provenance wording.**  
   Source-integrity verification yêu cầu authoritative `.sha256` sidecar được cung cấp làm formal provenance input. Digest tạo local chỉ được ghi informational; nếu thiếu sidecar thì provenance là `BLOCKED_AUTHORITATIVE_SIDECAR_MISSING` và run dừng.

3. **Modern Transformers dtype keyword trên runtime hỗ trợ, có compatibility handling.**  
   Model loading không còn truyền deprecated `torch_dtype` trên Transformers runtime hỗ trợ `dtype`. Capability-based selector chọn `dtype` khi installed `PreTrainedModel.from_pretrained` hỗ trợ và chỉ fallback legacy `torch_dtype` khi bắt buộc.

4. **Loại bỏ warning do tokenizer pad `max_length` dư thừa.**  
   Final dynamic `tokenizer.pad(...)` call của reranker không còn truyền `max_length=` bị ignore, loại bỏ warning về `max_length` khi `padding=True` mà không có truncation strategy, đồng thời giữ nguyên bounded output.

5. **Explicit embedding/reranker <=512-token regressions.**  
   Thêm fake-tokenizer regression tests gửi input dài hơn 512 token và assert tensor thực sự đi vào hai model bị bound ở 512, trailing pooling special token của embedding được giữ, Qwen reranker prompt/scoring structure không đổi và dynamic pad call không sinh warning.

## Qualified runtime defaults (không đổi)

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

## Performance — phase tiếp theo

Không có performance result được claim tại đây. Phase tiếp theo là performance-qualification campaign riêng, phải giữ `v0.1.0` làm control và thay một biến mỗi lần:

```text
FP16 control
-> BF16 candidate
-> thread count 2/4
-> reranker microbatch 1/2/4
-> measured K=2/5/10/20
-> only then Node/Qdrant integration decision
```

Node/Qdrant integration **không** bắt đầu bởi corrective release này.
