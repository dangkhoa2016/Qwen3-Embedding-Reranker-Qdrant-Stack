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
    assert "The first-public-release identity is:" not in text


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



def test_every_bilingual_markdown_pair_uses_standard_language_switch_below_h1():
    canonical = sorted(
        p for p in ROOT.rglob("*.md")
        if ".git" not in p.parts
        and ".pytest_cache" not in p.parts
        and not p.name.endswith(".vi.md")
        and p.with_name(p.name[:-3] + ".vi.md").is_file()
    )
    assert len(canonical) == 27
    for path in canonical:
        companion = path.with_name(path.name[:-3] + ".vi.md")
        en_lines = path.read_text(encoding="utf-8").splitlines()
        vi_lines = companion.read_text(encoding="utf-8").splitlines()
        en_h1 = next(i for i, line in enumerate(en_lines) if line.startswith("# "))
        vi_h1 = next(i for i, line in enumerate(vi_lines) if line.startswith("# "))
        expected_en = f"> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt]({companion.name})"
        expected_vi = f"> 🌐 Language / Ngôn ngữ: [English]({path.name}) | **Tiếng Việt**"
        assert en_lines[en_h1 + 1] == expected_en, path
        assert vi_lines[vi_h1 + 1] == expected_vi, companion
        assert [line for line in en_lines if "Language / Ngôn ngữ:" in line] == [expected_en]
        assert [line for line in vi_lines if "Language / Ngôn ngữ:" in line] == [expected_vi]
        assert not any(line.startswith("> English |") for line in en_lines)
        assert not any(
            line.startswith("> [English](")
            and "Tiếng Việt" in line
            and "Language / Ngôn ngữ:" not in line
            for line in vi_lines
        )


def test_readme_does_not_duplicate_first_public_release_identity_block():
    assert "The first-public-release identity is:" not in read("README.md")
    assert "The prepared first-public-release identity is:" not in read("README.md")
    assert "Public release identity đầu tiên là:" not in read("README.vi.md")



def test_public_readmes_do_not_expose_internal_qualification_identifiers():
    banned = [
        "v0.2.3c",
        "0.2.3rc1",
        "qwen_dual_server",
        "qwen3-dual-4b-cpu-rest-server",
    ]
    for path in ["README.md", "README.vi.md"]:
        text = read(path)
        for identifier in banned:
            assert identifier not in text, f"{path}: {identifier}"
    assert "Qualification evidence and provenance are documented in" in read("README.md")
    assert "Thông tin về quá trình kiểm chứng và nguồn gốc được ghi trong" in read("README.vi.md")


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


def test_release_facing_docs_are_publication_state_neutral_and_prepublish_notes_remain_historical():
    release_en = read("RELEASE_NOTES_v1.0.0.md")
    release_vi = read("RELEASE_NOTES_v1.0.0.vi.md")

    for required in [
        "SECURITY.md",
        "CONTRIBUTING.md",
        "## Publication channels",
        "Release identity: v1.0.0",
        "Package index / PyPI: separate publication channel",
    ]:
        assert required in release_en, required

    for path, banned in {
        "README.md": [
            "The `v1.0.0` tag and GitHub Release are not created yet",
        ],
        "README.vi.md": [
            "Tag `v1.0.0` và GitHub Release chưa được tạo",
        ],
        "RELEASE_NOTES_v1.0.0.md": [
            "first-release tag and GitHub Release pending",
            "no `v1.0.0` tag or GitHub Release has been created yet",
            "Tag `v1.0.0`: not created yet",
            "GitHub Release: not created yet",
            "Package index / PyPI: not published",
        ],
        "RELEASE_NOTES_v1.0.0.vi.md": [
            "first-release tag và GitHub Release đang chờ",
            "chưa tạo tag `v1.0.0` hoặc GitHub Release",
            "Tag `v1.0.0`: not created yet",
            "GitHub Release: not created yet",
            "Package index / PyPI: not published",
        ],
    }.items():
        text = read(path)
        for phrase in banned:
            assert phrase not in text, f"{path}: stale publication-state wording: {phrase}"

    assert "## Kênh phát hành" in release_vi
    assert "Release identity: v1.0.0" in release_vi
    assert "Package index / PyPI: kênh publication riêng" in release_vi

    for path in ["README.md", "README.vi.md", "RELEASE_NOTES_v1.0.0.md", "RELEASE_NOTES_v1.0.0.vi.md"]:
        evidence = read(path)
        assert "HISTORICAL_LOCAL_EXPANDED_SUITE=116 passed, 3 failed, 1 skipped" in evidence
        assert "BLOCKING_CI_SUITE=119 passed, 1 skipped, 3 deselected" in evidence
        assert "HISTORICAL_COMPATIBILITY_PROBES=executed separately" in evidence
        assert "BLOCKING_CI_SUITE=116 passed, 1 skipped, 3 deselected" not in evidence

    pre_en = read("PRE_PUBLISH_NOTES.md")
    pre_vi = read("PRE_PUBLISH_NOTES.vi.md")
    for notes in [pre_en, pre_vi]:
        assert "TAG=NONE" in notes
        assert "RELEASE=NONE" in notes
    assert "pre-tag publication checkpoint" in pre_en
    assert "pre-tag publication checkpoint" in pre_vi


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
