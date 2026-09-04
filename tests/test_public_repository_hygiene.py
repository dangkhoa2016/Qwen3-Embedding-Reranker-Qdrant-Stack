from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_python_310_toml_test_harness_declares_backport_and_fallback():
    dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert 'tomli>=2; python_version < "3.11"' in dev
    for path in ["tests/test_public_repository_hygiene.py", "tests/test_release_identity.py"]:
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "except ModuleNotFoundError:" in text
        assert "import tomli as tomllib" in text


def read(path: str) -> str:
    target = ROOT / path
    assert target.is_file(), f"missing public repository file: {path}"
    return target.read_text(encoding="utf-8")


def test_public_package_metadata_is_pep639_ready_and_url_safe():
    data = tomllib.loads(read("pyproject.toml"))
    project = data["project"]
    assert data["build-system"]["requires"][0].startswith("setuptools>=77")
    assert project["name"] == "qwen3-embedding-reranker-qdrant-stack"
    assert project["version"] == "1.0.0"
    assert project["readme"] == "README.md"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: MIT License" not in project.get("classifiers", [])
    assert "Programming Language :: Python :: 3" in project["classifiers"]
    assert "Topic :: Scientific/Engineering :: Artificial Intelligence" in project["classifiers"]
    assert {"qwen3-embedding", "qwen3-reranker", "qdrant", "text-embeddings", "reranking", "semantic-search", "vector-search", "information-retrieval", "retrieval", "cpu-inference", "gguf"}.issubset(set(project["keywords"]))
    assert project["urls"] == {
        "Homepage": "https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack",
        "Repository": "https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack",
        "Issues": "https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack/issues",
    }


def test_readme_is_a_complete_public_landing_page():
    text = read("README.md")
    for required in [
        "# Qwen3-Embedding-Reranker-Qdrant-Stack",
        "Package: qwen3-embedding-reranker-qdrant-stack",
        "## What this project provides",
        "## Installation",
        "## Quick start",
        "## API overview",
        "## Qualified Qdrant production demo",
        "## Security",
        "## Contributing",
        "## Known limitations",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "K5_DEFAULT=ACCEPT",
        "K2_FALLBACK=NOT_JUSTIFIED",
        "MAX_INSTRUCTION_CHARS=1024",
    ]:
        assert required in text, required
    assert "https://github.com/dangkhoa2016/Qwen3-Embedding-Reranker-Qdrant-Stack" in text


def test_security_policy_is_private_report_first_and_repository_aware():
    text = read("SECURITY.md")
    lower = text.lower()
    assert "i.am@dangkhoa.dev" in text
    assert "do not open a public issue" in lower
    assert "1.0.0" in text
    assert "github.com/dangkhoa2016/qwen3-embedding-reranker-qdrant-stack" in lower
    assert "ALLOW_INSECURE_NO_AUTH" in text
    assert "TRUST_PROXY_HEADERS" in text


def test_contributing_policy_preserves_qualification_boundary():
    text = read("CONTRIBUTING.md")
    for required in [
        "111 passed, 3 failed, 1 skipped",
        "116 passed, 3 failed, 1 skipped",
        "NEW_REGRESSION_FAILURES=0",
        "src/qwen_dual_server/config.py",
        "src/qwen_dual_server/gguf_reranker_engine.py",
        "src/qwen_dual_server/production_demo.py",
        "tests/test_gguf_reranker_engine.py",
        "tests/test_production_demo.py",
        "SECURITY.md",
    ]:
        assert required in text, required


def test_github_templates_and_community_files_are_complete_and_bilingual():
    required = [
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/bug_report.vi.md",
        ".github/ISSUE_TEMPLATE/documentation.md",
        ".github/ISSUE_TEMPLATE/documentation.vi.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/feature_request.vi.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE.vi.md",
        ".github/CODE_OF_CONDUCT.md",
        ".github/CODE_OF_CONDUCT.vi.md",
        ".github/SUPPORT.md",
        ".github/SUPPORT.vi.md",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/workflows/ci.yml",
    ]
    for path in required:
        assert (ROOT / path).is_file(), path
    assert "name: Bug report" in read(".github/ISSUE_TEMPLATE/bug_report.md")
    assert "name: Documentation" in read(".github/ISSUE_TEMPLATE/documentation.md")
    assert "name: Feature request" in read(".github/ISSUE_TEMPLATE/feature_request.md")
    assert "blank_issues_enabled: true" in read(".github/ISSUE_TEMPLATE/config.yml")
    assert "protected semantic" in read(".github/PULL_REQUEST_TEMPLATE.md").lower()
    assert "@dangkhoa2016" in read(".github/CODEOWNERS")
    dependabot = read(".github/dependabot.yml")
    assert 'package-ecosystem: "pip"' in dependabot
    assert 'package-ecosystem: "github-actions"' in dependabot


def test_every_canonical_markdown_file_has_a_vietnamese_companion():
    canonical = sorted(
        p for p in ROOT.rglob("*.md")
        if ".git" not in p.parts and ".pytest_cache" not in p.parts and not p.name.endswith(".vi.md")
    )
    assert canonical, "no canonical markdown files found"
    missing = []
    for path in canonical:
        companion = path.with_name(path.name[:-3] + ".vi.md")
        if not companion.is_file():
            missing.append(str(path.relative_to(ROOT)))
    assert not missing, "missing Vietnamese companions: " + ", ".join(missing)


def test_readme_badges_and_language_navigation_are_symmetric():
    en = read("README.md")
    vi = read("README.vi.md")
    badge_fragments = [
        "actions/workflows/ci.yml/badge.svg",
        "python-%3E%3D3.10",
        "license-MIT",
        "version-1.0.0",
        "Qdrant-1.18.3",
        "CPU-qualified",
    ]
    for fragment in badge_fragments:
        assert fragment in en, fragment
        assert fragment in vi, fragment
    assert "README.vi.md" in en
    assert "README.md" in vi
    assert "CI badge" in en
    assert "badge CI" in vi


def test_ci_workflow_uses_current_action_majors_and_baseline_isolation():
    ci = read(".github/workflows/ci.yml")
    assert "actions/checkout@v7" in ci
    assert "actions/setup-python@v7" in ci
    assert "actions/upload-artifact@v7" in ci
    assert "actions/cache@" not in ci
    assert "permissions:" in ci and "contents: read" in ci
    assert 'python-version: ["3.10", "3.12"]' in ci
    for nodeid in [
        "tests/test_engine_contracts.py::test_embedding_loader_is_cpu_fp16_low_memory_and_output_is_fp32",
        "tests/test_engine_contracts.py::test_reranker_uses_yes_no_protocol_and_sorts_results",
        "tests/test_engine_contracts.py::test_current_transformers_prefers_dtype_keyword",
    ]:
        assert nodeid in ci
    assert "continue-on-error: true" in ci
    assert "python -m build" in ci


def test_release_notes_reference_governance_files_and_current_repository_state():
    text = read("RELEASE_NOTES_v1.0.0.md")
    assert "SECURITY.md" in text
    assert "CONTRIBUTING.md" in text
    assert "Source publication to `main`: complete" in text
    assert "Tag `v1.0.0`: not created yet" in text
    assert "GitHub Release: not created yet" in text
    assert "Package index / PyPI: not published" in text
    assert "Status: local pre-publication draft." not in text


def test_readme_and_prepublish_notes_no_longer_claim_main_is_local_only():
    readme = read("README.md")
    notes = read("PRE_PUBLISH_NOTES.md")
    assert "current source remains a local pre-publication candidate" not in readme.lower()
    assert "PUBLICATION_STATE=GITHUB_SOURCE_PUBLISHED_ON_MAIN" in notes
    assert "MAIN_SOURCE=PUBLISHED" in notes
    assert "TAG=NONE" in notes
    assert "RELEASE=NONE" in notes


def test_sdist_manifest_includes_bilingual_core_governance_docs():
    text = read("MANIFEST.in")
    for path in [
        "SECURITY.md", "SECURITY.vi.md",
        "CONTRIBUTING.md", "CONTRIBUTING.vi.md",
        "README.vi.md",
    ]:
        assert f"include {path}" in text
