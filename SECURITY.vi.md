# Chính sách bảo mật
> 🌐 Language / Ngôn ngữ: [English](SECURITY.md) | **Tiếng Việt**

## Trạng thái hiện tại

Public repository: https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. Line `1.0.0` là first public release identity. Việc repository public không thay đổi yêu cầu phải báo unpatched vulnerability bằng kênh riêng.

Trước khi tạo tag `v1.0.0` đầu tiên, line `1.0.0` là release identity duy nhất đang được active review. Internal qualification labels như `v0.2.3c` và temporary local packaging label `0.2.3rc1` chưa từng là public releases và không phải supported public versions riêng.

Policy này cần review lại khi có supported release line mới hoặc dedicated private vulnerability-reporting channel.

## Báo cáo vulnerability

Vui lòng báo suspected vulnerabilities riêng tới:

```text
Đăng Khoa <i.am@dangkhoa.dev>
```

**Không mở public issue cho vulnerability chưa được patch.**

Một report hữu ích nên có, khi có thể:

- affected version hoặc source-candidate identity;
- OS, Python version và deployment topology;
- Transformers hay GGUF/llama.cpp reranker backend có liên quan không;
- minimal reproduction hoặc request sequence;
- expected so với observed behavior;
- security impact và realistic attack preconditions;
- sanitized logs/stack traces đã bỏ secrets.

Không gửi API keys, access tokens, private model credentials, private Qdrant credentials hoặc dữ liệu nhạy cảm không liên quan. Nếu cần evidence lớn, trước tiên mô tả nội dung cần chuyển và thỏa thuận kênh private phù hợp.

## Deployment security boundaries

### Authentication fail-closed mặc định

Service yêu cầu `DUAL_API_KEY` trừ khi insecure mode được bật rõ ràng:

```text
ALLOW_INSECURE_NO_AUTH=0
```

`ALLOW_INSECURE_NO_AUTH=1` bỏ qua bearer authentication và chỉ nên dùng cho controlled localhost testing. Không dùng cho internet-facing hoặc untrusted network deployment.

Dùng bearer token ngẫu nhiên mạnh, bảo vệ như secret, rotate nếu lộ và không đưa vào committed files/evidence bundles.

### Bind và TLS

Launcher bind `127.0.0.1` mặc định. Nó không thiết lập đầy đủ public TLS/security perimeter. Nếu cần remote access, đặt service sau trusted reverse proxy được cấu hình phù hợp hoặc private-network boundary khác và cung cấp TLS tại đó.

### Proxy headers và rate limiting

`TRUST_PROXY_HEADERS=1` cho phép application dùng `X-Forwarded-For` để xác định client identity cho fixed-window rate limiter.

Chỉ bật khi trusted proxy sanitize forwarding headers. Nếu client có thể truy cập trực tiếp application hoặc gửi forwarding headers không đáng tin, đặt:

```text
TRUST_PROXY_HEADERS=0
```

Built-in rate limiter là local application safeguard, không phải comprehensive DoS protection.

### Public operational endpoints

`GET /health` và `GET /ready` chủ đích không auth. Các `/v1/*` endpoint còn lại yêu cầu bearer auth mặc định. Áp dụng network controls nếu ngay cả liveness/readiness exposure cũng không phù hợp môi trường.

### External artifacts

Model weights, GGUF binaries, llama.cpp runtime files và Qdrant snapshot là external artifacts. Khi có qualified identity, hãy verify hash/provenance mong đợi trước khi dùng. Xem untrusted model/runtime/database artifacts như supply-chain inputs, không phải inert data.

Qualified production demo ghi exact artifact identities trong `STAGE2_R10_QUALIFICATION.vi.md`/`.md` và `PRODUCTION_DEMO_PROVENANCE.vi.md`/`.md`.

### Secrets và evidence

Evidence collector được thiết kế redact `DUAL_API_KEY`, nhưng operator vẫn phải inspect logs/evidence trước khi chia sẻ. Không giả định arbitrary environment variables, proxy credentials, Qdrant keys, shell history hoặc external-tool logs tự động an toàn để public.

## Security-sensitive changes

Thay đổi authentication, request limits, proxy-header handling, process isolation, model/runtime loading, Qdrant connectivity hoặc protected Stage-II semantic files cần security review tương ứng impact. Documentation-only/publication-hygiene change không được âm thầm thay đổi các behavior đó.
