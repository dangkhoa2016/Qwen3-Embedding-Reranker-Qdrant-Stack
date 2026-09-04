# Security Policy
> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](SECURITY.vi.md)

## Current status

The public repository is https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack. The `1.0.0` line is the first public release identity. Public repository availability does not change the requirement to report unpatched vulnerabilities privately.

Before the first `v1.0.0` tag is created, the `1.0.0` line is the only actively reviewed release identity. Internal qualification labels such as `v0.2.3c` and the temporary local packaging label `0.2.3rc1` were never public releases and are not separate supported public versions.

This policy should be reviewed again when an additional supported release line or a dedicated private vulnerability-reporting channel is introduced.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to:

```text
Đăng Khoa <i.am@dangkhoa.dev>
```

**Do not open a public issue for an unpatched vulnerability.**

A useful report includes, where possible:

- affected version or source-candidate identity;
- operating system, Python version, and deployment topology;
- whether the Transformers or GGUF/llama.cpp reranker backend is involved;
- a minimal reproduction or request sequence;
- expected versus observed behavior;
- security impact and realistic attack preconditions;
- sanitized logs or stack traces with secrets removed.

Do not send API keys, access tokens, private model credentials, private Qdrant credentials, or unrelated sensitive data. If large evidence is needed, first describe what needs to be transferred and arrange an appropriate private channel.

## Deployment security boundaries

### Authentication is fail-closed by default

The service requires `DUAL_API_KEY` unless insecure mode is explicitly enabled:

```text
ALLOW_INSECURE_NO_AUTH=0
```

`ALLOW_INSECURE_NO_AUTH=1` bypasses bearer authentication and should be used only for controlled localhost testing. Do not use it for an internet-facing or otherwise untrusted network deployment.

Use a strong randomly generated bearer token, protect it as a secret, rotate it if exposed, and do not place it in committed files or evidence bundles.

### Bind and TLS

The supplied launcher binds to `127.0.0.1` by default. It does not establish a complete public TLS/security perimeter. If remote access is required, place the service behind an appropriately configured trusted reverse proxy or another private-network boundary and provide TLS there.

### Proxy headers and rate limiting

`TRUST_PROXY_HEADERS=1` allows the application to use `X-Forwarded-For` when determining the client identity for its fixed-window rate limiter.

Keep this enabled only when a trusted proxy sanitizes forwarding headers. If clients can reach the application directly or can supply untrusted forwarding headers, set:

```text
TRUST_PROXY_HEADERS=0
```

The built-in rate limiter is a local application safeguard, not comprehensive denial-of-service protection.

### Public operational endpoints

`GET /health` and `GET /ready` are intentionally unauthenticated. The remaining `/v1/*` endpoints require bearer authentication by default. Apply network controls if even liveness/readiness exposure is inappropriate for your environment.

### External artifacts

Model weights, GGUF binaries, llama.cpp runtime files, and the Qdrant snapshot are external artifacts. Verify expected hashes/provenance before use where a qualified identity is provided. Treat untrusted model/runtime/database artifacts as supply-chain inputs, not inert data.

The qualified production demo documents specific artifact identities in `STAGE2_R10_QUALIFICATION.md` and `PRODUCTION_DEMO_PROVENANCE.md`.

### Secrets and evidence

The evidence collector is designed to redact `DUAL_API_KEY`, but operators should still inspect logs and evidence before sharing them. Do not assume arbitrary environment variables, proxy credentials, Qdrant keys, shell history, or external-tool logs are automatically safe to publish.

## Security-sensitive changes

Changes to authentication, request limits, proxy-header handling, process isolation, model/runtime loading, Qdrant connectivity, or the protected Stage-II semantic files require security review appropriate to their impact. A documentation-only/publication-hygiene change must not silently alter those behaviors.
