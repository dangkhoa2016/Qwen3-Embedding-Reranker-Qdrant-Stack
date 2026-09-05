from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.is_file(), f"missing public repository file: {path}"
    return target.read_text(encoding="utf-8")


def test_public_package_metadata_is_current():
    project = tomllib.loads(read("pyproject.toml"))["project"]
    assert project["name"] == "qwen3-embedding-reranker-qdrant-stack"
    assert project["version"] == "1.0.0"
    assert project["authors"] == [{"name": "Đăng Khoa", "email": "i.am@dangkhoa.dev"}]
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert project["readme"] == "README.md"


def test_public_landing_and_governance_docs_are_complete():
    readme = read("README.md")
    for required in [
        "## What this project provides", "## Production qualification",
        "## Installation", "## Quick start", "## API overview",
        "## Qualified Qdrant production demo", "## Security",
        "## Contributing", "## Known limitations",
        "PRODUCTION_QUALIFICATION.md", "PRODUCTION_DEMO_PROVENANCE.md",
        "Retrieval default: K=5", "MAX_INSTRUCTION_CHARS=1024",
    ]:
        assert required in readme, required

    security = read("SECURITY.md")
    assert "Do not open a public issue" in security
    assert "i.am@dangkhoa.dev" in security
    assert "ALLOW_INSECURE_NO_AUTH" in security
    assert "TRUST_PROXY_HEADERS" in security

    contributing = read("CONTRIBUTING.md")
    for required in [
        "Retrieval default: K=5", "MAX_INSTRUCTION_CHARS=1024",
        "src/qwen_dual_server/config.py",
        "src/qwen_dual_server/gguf_reranker_engine.py",
        "src/qwen_dual_server/production_demo.py",
    ]:
        assert required in contributing, required


def test_current_public_tree_excludes_historical_development_docs():
    removed = [
        "BASELINE_PROVENANCE.txt",
        "OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.md",
        "OPENCODE_QWEN3_DUAL_4B_CPU_SERVER_KAGGLE_RUNBOOK_2026-08-30.vi.md",
        "PRE" + "_PUBLISH_NOTES.md", "PRE" + "_PUBLISH_NOTES.vi.md",
        "README_INT8_EXPERIMENT.md", "README_INT8_EXPERIMENT.vi.md",
        "STAGE2" + "_R10_QUALIFICATION.md", "STAGE2" + "_R10_QUALIFICATION.vi.md",
        "docs/hybrid-gguf", "docs/superpowers",
    ]
    for rel in removed:
        assert not (ROOT / rel).exists(), rel


def test_current_public_docs_do_not_expose_internal_development_labels():
    banned = [
        "v0" + ".2.3c", "0.2.3" + "rc1", "Stage" + "-II",
        "STAGE2" + "_R10", "STAGE2" + "_R3_TO_R10", "R3" + "→R10",
        "K5" + "_DEFAULT=ACCEPT", "K2" + "_FALLBACK=NOT_JUSTIFIED",
        "FINAL" + "_RELEASE_DEFAULT=K5_READY",
        "qwen3" + "-dual-4b",
        "DUAL" + "_4B_TRANSFORMERS_TORCHAO_INT8",
        "Experimental" + " copy only",
        "FALLBACK" + "_TO_K2",
    ]
    paths = list(ROOT.rglob("*.md")) + [ROOT / "VERIFICATION_SUMMARY.txt"]
    for path in paths:
        if ".git" in path.parts or ".pytest_cache" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for value in banned:
            assert value not in text, f"{path.relative_to(ROOT)}: {value}"


def test_public_qualification_and_provenance_are_outcome_based():
    qualification = read("PRODUCTION_QUALIFICATION.md")
    for required in [
        "Production qualification: PASS", "Retrieval default: K=5",
        "Semantic validation: 3/3 PASS", "Verified Run All: 594.964s",
        "Qdrant version=1.18.3",
    ]:
        assert required in qualification, required

    provenance = read("PRODUCTION_DEMO_PROVENANCE.md")
    assert "Version=1.0.0" in provenance
    assert "snapshot SHA256=71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f" in provenance


def test_every_markdown_file_has_a_vietnamese_companion_and_standard_switch():
    canonical = sorted(
        p for p in ROOT.rglob("*.md")
        if ".git" not in p.parts
        and ".pytest_cache" not in p.parts
        and not p.name.endswith(".vi.md")
    )
    assert canonical
    for path in canonical:
        companion = path.with_name(path.name[:-3] + ".vi.md")
        assert companion.is_file(), path
        en = path.read_text(encoding="utf-8").splitlines()
        vi = companion.read_text(encoding="utf-8").splitlines()
        en_h1 = next(i for i, line in enumerate(en) if line.startswith("# "))
        vi_h1 = next(i for i, line in enumerate(vi) if line.startswith("# "))
        assert en[en_h1 + 1] == f"> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt]({companion.name})"
        assert vi[vi_h1 + 1] == f"> 🌐 Language / Ngôn ngữ: [English]({path.name}) | **Tiếng Việt**"


def test_github_community_and_ci_files_are_current():
    for path in [
        ".github/PULL_REQUEST_TEMPLATE.md", ".github/PULL_REQUEST_TEMPLATE.vi.md",
        ".github/CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.vi.md",
        ".github/SUPPORT.md", ".github/SUPPORT.vi.md",
        ".github/CODEOWNERS", ".github/dependabot.yml", ".github/workflows/ci.yml",
    ]:
        assert (ROOT / path).is_file(), path

    ci = read(".github/workflows/ci.yml")
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in ci
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in ci
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7" in ci
    assert 'python-version: ["3.10", "3.12"]' in ci
    assert "continue-on-error: true" not in ci
    assert "--deselect=" not in ci
    assert "- name: Run full regression suite" in ci
    assert "run: pytest -q" in ci
    assert "- name: Upload canonical tag distributions" in ci
    assert "if: startsWith(github.ref, 'refs/tags/v')" in ci
    assert "python -m build" in ci
    issue_config = read(".github/ISSUE_TEMPLATE/config.yml")
    assert "blank_issues_enabled: false" in issue_config
    assert read(".github/CODEOWNERS").startswith("# Default repository owner.")


def test_release_notes_are_current_and_bilingual():
    en = read("RELEASE_NOTES_v1.0.0.md")
    vi = read("RELEASE_NOTES_v1.0.0.vi.md")
    for required in [
        "## Production qualification", "## Verification",
        "## Publication channels", "Release identity: v1.0.0",
    ]:
        assert required in en, required
    assert "## Kiểm chứng production" in vi
    assert "## Xác minh" in vi
    assert "## Kênh phát hành" in vi
    for text in [en, vi, read("README.md"), read("README.vi.md")]:
        assert "TAG=NONE" not in text
        assert "RELEASE=NONE" not in text
        assert "pre-tag" not in text.lower()


def test_sdist_manifest_includes_bilingual_core_governance_docs():
    manifest = read("MANIFEST.in")
    for path in [
        "README.vi.md", "SECURITY.md", "SECURITY.vi.md",
        "CONTRIBUTING.md", "CONTRIBUTING.vi.md",
    ]:
        assert f"include {path}" in manifest


def test_tracked_paths_and_utf8_text_are_free_of_retired_internal_labels():
    import subprocess

    retired_path_tokens = [
        "v0" + "23",
        "v0" + "23c",
        "pre" + "_publish",
        "pre" + "-publish",
        "stage2" + "_r10",
        "qwen3" + "-dual-4b",
    ]
    retired_content_tokens = [
        "v0" + ".1.0",
        "v0" + ".1.1",
        "v0" + ".2.3",
        "v0" + "23",
        "v0" + "23c",
        "Stage" + "-II",
        "STAGE2" + "_R10",
        "STAGE2" + "_R3_TO_R10",
        "R3" + "→R10",
        "EXPECTED" + "_H3",
        "NATIVE" + "_INSTRUCTION_RED",
        "K5" + "_DEFAULT=ACCEPT",
        "K2" + "_FALLBACK=NOT_JUSTIFIED",
        "FINAL" + "_RELEASE_DEFAULT=K5_READY",
        "qwen3" + "-dual-4b",
        "DUAL" + "_4B_TRANSFORMERS_TORCHAO_INT8",
        "Experimental" + " copy only",
        "FALLBACK" + "_TO_K2",
    ]

    tracked = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0")
    for rel in filter(None, tracked):
        lowered = rel.lower()
        for token in retired_path_tokens:
            assert token not in lowered, f"retired path token {token!r}: {rel}"

        data = (ROOT / rel).read_bytes()
        if b"\0" in data[:8192]:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for token in retired_content_tokens:
            assert token not in text, f"retired content token {token!r}: {rel}"
