from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> str:
    path = ROOT / name
    assert path.is_file(), f"missing publication file: {name}"
    return path.read_text(encoding="utf-8")


def test_instruction_capacity_is_1024():
    assert "MAX_INSTRUCTION_CHARS=1024" in read(".env.example")


def test_public_docs_record_verified_k5_default_without_internal_labels():
    for name in (
        "README.md",
        "README_PRODUCTION_DEMO.md",
        "README_PRODUCTION_DEMO.vi.md",
        "guide-production-demo.md",
        "PRODUCTION_QUALIFICATION.md",
    ):
        text = read(name)
        assert "K=5" in text, name
        assert "K5" + "_DEFAULT=ACCEPT" not in text, name
        assert "K2" + "_FALLBACK=NOT_JUSTIFIED" not in text, name


def test_public_production_qualification_record_is_present():
    text = read("PRODUCTION_QUALIFICATION.md")
    assert "Production qualification: PASS" in text
    assert "Retrieval default: K=5" in text
    assert "Semantic validation: 3/3 PASS" in text
    assert "Verified Run All: 594.964s" in text


def test_obsolete_publication_checkpoint_files_are_absent_from_current_tree():
    legacy = "PRE" + "_PUBLISH_NOTES"
    assert not (ROOT / f"{legacy}.md").exists()
    assert not (ROOT / f"{legacy}.vi.md").exists()


def test_no_egg_info_residue_in_source_tree():
    assert not list((ROOT / "src").glob("*.egg-info"))


def test_release_notes_are_publication_state_neutral_and_bilingual():
    release_en = read("RELEASE_NOTES_v1.0.0.md")
    release_vi = read("RELEASE_NOTES_v1.0.0.vi.md")

    for required in [
        "## Publication channels",
        "Release identity: v1.0.0",
        "GitHub Release: tagged release channel for canonical release assets",
        "Package index / PyPI: separate publication channel",
        "Publication through one channel does not imply publication through another; each channel is verified independently.",
    ]:
        assert required in release_en, required

    for required in [
        "## Kênh phát hành",
        "Release identity: v1.0.0",
        "GitHub Release: kênh release theo tag cho canonical release assets",
        "Package index / PyPI: kênh publication riêng",
        "Publication qua một kênh không đồng nghĩa đã publication qua kênh khác; từng kênh được kiểm chứng độc lập.",
    ]:
        assert required in release_vi, required

    for stale in [
        "TAG=NONE",
        "RELEASE=NONE",
        "first-release tag and GitHub Release pending",
        "no `v1.0.0` tag or GitHub Release has been created yet",
    ]:
        assert stale not in release_en
        assert stale not in release_vi
