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


def test_pre_publish_notes_preserve_unpublished_state():
    text = read("PRE_PUBLISH_NOTES.md").lower()
    assert "local" in text
    assert "unpublished" in text or "not yet been published" in text
    assert "no remote" in text


def test_no_egg_info_residue_in_source_tree():
    assert not list((ROOT / "src").glob("*.egg-info"))


def test_release_notes_are_explicitly_prepublication():
    text = read("RELEASE_NOTES_v1.0.0.md")
    assert "Status: local pre-publication draft." in text
    assert "no remote repository, tag, or release" in text
