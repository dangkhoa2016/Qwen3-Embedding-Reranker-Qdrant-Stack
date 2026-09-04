---
name: Bug report
about: Report a reproducible defect in the service, tooling, or production demo
title: "[Bug] "
labels: ""
assignees: ""
---

## Summary

Describe the defect and its impact.

## Environment

- Source/package version:
- Python version:
- Operating system / environment:
- PyTorch version:
- Reranker backend (`transformers` or `llama_cpp`):
- Qdrant version, if relevant:

## Steps to reproduce

1.
2.
3.

## Expected behavior

What did you expect to happen?

## Actual behavior

What happened instead?

## Relevant logs/evidence

Paste only sanitized output. Remove API keys, tokens, private model credentials, Qdrant credentials, and unrelated sensitive data.

## Qualification impact

Does this appear to affect the qualified production-demo semantics, K=5 behavior, authentication/fail-closed behavior, OOM/timing gates, or one of the protected semantic files? If yes, explain why.

> Security vulnerability? Do not file it here. Follow `SECURITY.md` and report it privately.
