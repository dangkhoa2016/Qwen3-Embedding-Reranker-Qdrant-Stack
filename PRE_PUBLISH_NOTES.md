# Local pre-publication notes

This source tree is a **local, unpublished** preparation candidate for the first public release of `qwen3-dual-4b-cpu-rest-server`.

```text
PUBLIC_VERSION=1.0.0
AUTHOR=Đăng Khoa <i.am@dangkhoa.dev>
LICENSE=MIT
PUBLICATION_STATE=UNPUBLISHED
REMOTE_REPOSITORY=NONE
GITHUB_REPOSITORY=NONE
TAG=NONE
RELEASE=NONE
```

There is no remote repository, public branch, tag, GitHub Release, PyPI publication, or other package publication implied by this candidate.

Internal labels `v0.2.3c` and `0.2.3rc1` are provenance only and were never public versions.

## Qualification boundary

Stage-II R10 is closed. Do not reopen H1/H2 experiments, K=2 fallback evaluation, alternate quantization campaigns, or the R3→R10 corrective chain without new evidence that directly invalidates the accepted qualification.

## Protected semantics

The five qualified semantic files listed in `PRODUCTION_DEMO_PROVENANCE.md` must remain byte-identical during publication-hygiene edits.

## Known regression baseline

```text
110 passed
3 failed
1 skipped
KNOWN_BASELINE_FAILURES=3
NEW_REGRESSION_FAILURES=0
FULL_REGRESSION_BASELINE_MATCH=PASS
```

Do not rewrite this as “all tests pass.” Any change in the failure set requires investigation before packaging.


## Public-facing repository/package audit

The local public-facing audit added/refined `README.md`, PEP 639 package metadata, `SECURITY.md`, `CONTRIBUTING.md`, and local `.github` issue/pull-request templates. No repository URL was invented and no remote action was performed.

```text
PUBLIC_FACING_REPOSITORY_AUDIT=PASS
GITHUB_TEMPLATES_PREPARED_LOCAL_ONLY=YES
CODE_OF_CONDUCT_DEFERRED=YES
DEPENDABOT_DEFERRED_UNTIL_REPOSITORY_POLICY=YES
PROJECT_URLS=OMITTED_UNTIL_REAL_URLS_EXIST
```
