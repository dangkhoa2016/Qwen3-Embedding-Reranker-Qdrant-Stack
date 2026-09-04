from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_first_public_release_identity():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert project["name"] == "qwen3-dual-4b-cpu-rest-server"
    assert project["version"] == "1.0.0"
    assert project["authors"] == [{"name": "Đăng Khoa", "email": "i.am@dangkhoa.dev"}]
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: MIT License" not in project["classifiers"]


def test_runtime_version_is_1_0_0():
    namespace = {}
    exec((ROOT / "src/qwen_dual_server/__init__.py").read_text(encoding="utf-8"), namespace)
    assert namespace["__version__"] == "1.0.0"


def test_mit_license_identifies_author_and_year():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8") if (ROOT / "LICENSE").exists() else ""
    assert text.startswith("MIT License")
    assert "Copyright (c) 2026 Đăng Khoa" in text
    assert "Permission is hereby granted, free of charge" in text
