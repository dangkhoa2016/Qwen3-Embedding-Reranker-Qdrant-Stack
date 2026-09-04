from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    path = ROOT / name
    assert path.is_file(), f"missing publication file: {name}"
    return path.read_text(encoding="utf-8")


def test_instruction_capacity_is_1024():
    assert "MAX_INSTRUCTION_CHARS=1024" in read(".env.example")


def test_public_docs_record_verified_k5_decision():
    for name in ("README.md", "README_PRODUCTION_DEMO.md", "README_PRODUCTION_DEMO.vi.md", "guide-production-demo.md"):
        text = read(name)
        assert "K5_DEFAULT=ACCEPT" in text, name
        assert "K2_FALLBACK=NOT_JUSTIFIED" in text, name


def test_stage2_r10_qualification_record_is_present():
    text = read("STAGE2_R10_QUALIFICATION.md")
    assert "STAGE2_R10_QUALIFICATION=PASS" in text
    assert "STAGE2_R3_TO_R10=CLOSED" in text
    assert "FINAL_RELEASE_DEFAULT=K5_READY" in text


def test_pre_publish_notes_record_source_published_pre_tag_state():
    text = read("PRE_PUBLISH_NOTES.md")
    assert "PUBLICATION_STATE=GITHUB_SOURCE_PUBLISHED_ON_MAIN" in text
    assert "MAIN_SOURCE=PUBLISHED" in text
    assert "TAG=NONE" in text
    assert "RELEASE=NONE" in text
    assert "package-index publication" in text.lower()


def test_no_egg_info_residue_in_source_tree():
    assert not list((ROOT / "src").glob("*.egg-info"))


def test_release_notes_record_source_published_pre_tag_state():
    text = read("RELEASE_NOTES_v1.0.0.md")
    assert "Status: GitHub source published on `main`; first-release tag and GitHub Release pending." in text
    assert "Source publication to `main`: complete" in text
    assert "Tag `v1.0.0`: not created yet" in text
    assert "GitHub Release: not created yet" in text
    assert "Package index / PyPI: not published" in text
