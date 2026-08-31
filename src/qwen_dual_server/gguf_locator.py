from __future__ import annotations

from pathlib import Path


DEFAULT_RERANKER_GGUF_BASENAME = "Qwen3-Reranker-4B.Q4_K_M.gguf"


class GGUFResolutionError(RuntimeError):
    pass


def _validate_explicit(path: Path) -> Path:
    if path.suffix.lower() != ".gguf":
        raise GGUFResolutionError(f"reranker GGUF path must end in .gguf: {path}")
    if not path.is_file():
        raise GGUFResolutionError(f"reranker GGUF file does not exist: {path}")
    return path


def resolve_reranker_gguf(
    explicit_path: str | Path | None,
    kaggle_input_root: str | Path = "/kaggle/input",
    preferred_basename: str = DEFAULT_RERANKER_GGUF_BASENAME,
) -> Path:
    """Resolve exactly one preferred reranker GGUF without quant fallback."""
    if explicit_path is not None and str(explicit_path).strip():
        return _validate_explicit(Path(explicit_path).expanduser())

    root = Path(kaggle_input_root)
    if not root.is_dir():
        raise GGUFResolutionError(f"Kaggle input root does not exist: {root}")

    exact = sorted(path for path in root.rglob(preferred_basename) if path.is_file())
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        joined = ", ".join(str(path) for path in exact)
        raise GGUFResolutionError(
            f"multiple exact {preferred_basename} matches found; set RERANKER_GGUF_PATH explicitly: {joined}"
        )

    available = sorted(
        path for path in root.rglob("Qwen3-Reranker-4B*.gguf") if path.is_file()
    )
    listing = ", ".join(str(path) for path in available) if available else "none"
    raise GGUFResolutionError(
        f"preferred GGUF {preferred_basename} was not found under {root}; "
        f"available Qwen3-Reranker-4B GGUF files: {listing}. "
        "No alternate quant is selected automatically."
    )
