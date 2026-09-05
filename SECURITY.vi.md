# Chính sách bảo mật
> 🌐 Language / Ngôn ngữ: [English](SECURITY.md) | **Tiếng Việt**

## Trạng thái hiện tại

Public repository là https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. Supported public release line là `1.0.0`.

Policy này cần review khi có supported release line mới hoặc dedicated private vulnerability-reporting channel.

## Báo cáo vulnerability

Vui lòng báo suspected vulnerabilities riêng tới:

```text
Đăng Khoa <i.am@dangkhoa.dev>
```

**Không mở public issue cho vulnerability chưa được patch.**

Một report hữu ích nên có, khi có thể:

- affected version;
- OS, Python version và deployment topology;
- Transformers hay GGUF/llama.cpp reranker backend có liên quan không;
- minimal reproduction hoặc request sequence;
- expected so với observed behavior;
- security impact và realistic attack preconditions;
- sanitized logs hoặc stack traces đã bỏ secrets.

Không gửi API keys, access tokens, private model credentials, private Qdrant credentials hoặc dữ liệu nhạy cảm không liên quan.

## Deployment security boundaries

### Authentication fail-closed mặc định

Service yêu cầu `DUAL_API_KEY` trừ khi insecure mode được bật rõ ràng:

```text
ALLOW_INSECURE_NO_AUTH=0
```

`ALLOW_INSECURE_NO_AUTH=1` bỏ qua bearer authentication và chỉ nên dùng cho controlled localhost testing.

Dùng bearer token ngẫu nhiên mạnh, bảo vệ như secret, rotate nếu lộ và không đưa vào committed files hoặc evidence bundles.

### Bind và TLS

Launcher bind `127.0.0.1` mặc định. Nó không thiết lập đầy đủ public TLS/security perimeter. Nếu cần remote access, đặt service sau trusted reverse proxy được cấu hình phù hợp hoặc private-network boundary khác và cung cấp TLS tại đó.

### Proxy headers và rate limiting

`TRUST_PROXY_HEADERS=1` cho phép application dùng `X-Forwarded-For` cho client identity trong fixed-window rate limiter.

Chỉ bật khi trusted proxy sanitize forwarding headers. Nếu không, đặt:

```text
TRUST_PROXY_HEADERS=0
```

Built-in rate limiter là local application safeguard, không phải comprehensive denial-of-service protection.

### Public operational endpoints

`GET /health` và `GET /ready` chủ đích không auth. Các `/v1/*` endpoint còn lại yêu cầu bearer auth mặc định. Áp dụng network controls nếu ngay cả liveness/readiness exposure cũng không phù hợp.

### External artifacts

Model weights, GGUF binaries, llama.cpp runtime files và Qdrant snapshot là external artifacts. Khi có qualified identity, hãy verify expected hashes/provenance trước khi dùng. Xem untrusted model/runtime/database artifacts như supply-chain inputs.

Verified production-demo artifact identities nằm trong `PRODUCTION_QUALIFICATION.vi.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`.

### Secrets và evidence

Evidence collector được thiết kế redact `DUAL_API_KEY`, nhưng operator vẫn phải inspect logs/evidence trước khi chia sẻ. Không giả định arbitrary environment variables, proxy credentials, Qdrant keys, shell history hoặc external-tool logs tự động an toàn để public.

## Security-sensitive changes

Thay đổi authentication, request limits, proxy-header handling, process isolation, model/runtime loading, Qdrant connectivity hoặc qualification-sensitive runtime files cần security review phù hợp impact. Documentation-only changes không được âm thầm thay đổi các behavior đó.
