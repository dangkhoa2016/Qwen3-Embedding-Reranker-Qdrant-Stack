from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.is_file(), f"missing public repository file: {path}"
    return target.read_text(encoding="utf-8")


def test_public_package_metadata_is_pep639_ready_and_url_safe():
    data = tomllib.loads(read("pyproject.toml"))
    project = data["project"]
    assert data["build-system"]["requires"][0].startswith("setuptools>=77")
    assert project["name"] == "qwen3-dual-4b-cpu-rest-server"
    assert project["version"] == "1.0.0"
    assert project["readme"] == "README.md"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: MIT License" not in project.get("classifiers", [])
    assert "Programming Language :: Python :: 3" in project["classifiers"]
    assert "Topic :: Scientific/Engineering :: Artificial Intelligence" in project["classifiers"]
    assert {"qwen3", "embedding", "reranking", "qdrant", "cpu"}.issubset(set(project["keywords"]))
    assert "urls" not in project, "do not invent project URLs before a real public repository exists"


def test_readme_is_a_complete_public_landing_page():
    text = read("README.md")
    for required in [
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
    assert "github.com/" not in text.lower(), "README must not invent a repository URL"


def test_security_policy_is_private_report_first_and_unpublished_aware():
    text = read("SECURITY.md")
    lower = text.lower()
    assert "i.am@dangkhoa.dev" in text
    assert "do not open a public issue" in lower
    assert "1.0.0" in text
    assert "unpublished" in lower or "pre-publication" in lower
    assert "ALLOW_INSECURE_NO_AUTH" in text
    assert "TRUST_PROXY_HEADERS" in text


def test_contributing_policy_preserves_qualification_boundary():
    text = read("CONTRIBUTING.md")
    for required in [
        "110 passed, 3 failed, 1 skipped",
        "NEW_REGRESSION_FAILURES=0",
        "src/qwen_dual_server/config.py",
        "src/qwen_dual_server/gguf_reranker_engine.py",
        "src/qwen_dual_server/production_demo.py",
        "tests/test_gguf_reranker_engine.py",
        "tests/test_production_demo.py",
        "SECURITY.md",
    ]:
        assert required in text, required


def test_local_github_templates_exist_without_remote_assumptions():
    bug = read(".github/ISSUE_TEMPLATE/bug_report.md")
    docs = read(".github/ISSUE_TEMPLATE/documentation.md")
    config = read(".github/ISSUE_TEMPLATE/config.yml")
    pr = read(".github/PULL_REQUEST_TEMPLATE.md")
    assert "name: Bug report" in bug
    assert "name: Documentation" in docs
    assert "blank_issues_enabled: true" in config
    assert "protected semantic" in pr.lower()
    joined = "\n".join([bug, docs, config, pr]).lower()
    assert "github.com/" not in joined


def test_release_notes_reference_governance_files_without_claiming_publication():
    text = read("RELEASE_NOTES_v1.0.0.md")
    assert "SECURITY.md" in text
    assert "CONTRIBUTING.md" in text
    assert "Status: local pre-publication draft." in text
    assert "no remote repository, tag, or release" in text


def test_sdist_manifest_includes_core_governance_docs():
    text = read("MANIFEST.in")
    assert "include SECURITY.md" in text
    assert "include CONTRIBUTING.md" in text
