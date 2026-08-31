from pathlib import Path
import pytest

from qwen_dual_server.gguf_locator import GGUFResolutionError, resolve_reranker_gguf

PREFERRED = "Qwen3-Reranker-4B.Q4_K_M.gguf"


def test_explicit_path_wins(tmp_path: Path):
    explicit = tmp_path / PREFERRED
    explicit.write_bytes(b"gguf")
    other = tmp_path / "nested" / PREFERRED
    other.parent.mkdir()
    other.write_bytes(b"other")
    assert resolve_reranker_gguf(str(explicit), tmp_path, PREFERRED) == explicit


def test_exact_q4_k_m_auto_match_succeeds(tmp_path: Path):
    model = tmp_path / "models" / "mirror" / PREFERRED
    model.parent.mkdir(parents=True)
    model.write_bytes(b"gguf")
    assert resolve_reranker_gguf(None, tmp_path, PREFERRED) == model


def test_zero_candidates_fail_with_available_listing(tmp_path: Path):
    alt = tmp_path / "Qwen3-Reranker-4B.Q5_K_M.gguf"
    alt.write_bytes(b"gguf")
    with pytest.raises(GGUFResolutionError, match="Q4_K_M") as exc:
        resolve_reranker_gguf(None, tmp_path, PREFERRED)
    assert "Q5_K_M" in str(exc.value)


def test_multiple_exact_matches_fail(tmp_path: Path):
    for name in ("a", "b"):
        p = tmp_path / name / PREFERRED
        p.parent.mkdir()
        p.write_bytes(b"gguf")
    with pytest.raises(GGUFResolutionError, match="multiple"):
        resolve_reranker_gguf(None, tmp_path, PREFERRED)


def test_does_not_silently_select_other_quant(tmp_path: Path):
    alt = tmp_path / "Qwen3-Reranker-4B.Q8_0.gguf"
    alt.write_bytes(b"gguf")
    with pytest.raises(GGUFResolutionError):
        resolve_reranker_gguf(None, tmp_path, PREFERRED)
