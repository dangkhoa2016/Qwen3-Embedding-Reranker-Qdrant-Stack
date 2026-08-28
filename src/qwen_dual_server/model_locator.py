from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

ModelRole = Literal["embedding", "reranker"]


class ModelResolutionError(RuntimeError):
    pass


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ModelResolutionError(f"invalid JSON: {path}: {exc}") from exc


def _role_from_modules(modules: object) -> str | None:
    if not isinstance(modules, list):
        return None
    types = [str(item.get("type", "")) for item in modules if isinstance(item, dict)]
    if any("LogitScore" in item for item in types):
        return "reranker"
    if any("Pooling" in item for item in types):
        return "embedding"
    return None


def validate_model_root(root: Path, role: ModelRole) -> Path:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ModelResolutionError(f"model root is not a directory: {root}")

    config_path = root / "config.json"
    index_path = root / "model.safetensors.index.json"
    modules_path = root / "modules.json"
    tokenizer_path = root / "tokenizer_config.json"
    for required in (config_path, index_path, modules_path, tokenizer_path):
        if not required.is_file():
            raise ModelResolutionError(f"missing required model file: {required}")

    config = _load_json(config_path)
    if not isinstance(config, dict):
        raise ModelResolutionError(f"config.json is not an object: {root}")
    expected = {
        "model_type": "qwen3",
        "hidden_size": 2560,
        "num_hidden_layers": 36,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise ModelResolutionError(f"unexpected {key}={config.get(key)!r} in {root}; expected {value!r}")

    modules = _load_json(modules_path)
    observed_role = _role_from_modules(modules)
    if observed_role != role:
        raise ModelResolutionError(
            f"model role mismatch for {root}: observed={observed_role!r}, expected={role!r}"
        )

    index = _load_json(index_path)
    if not isinstance(index, dict) or not isinstance(index.get("weight_map"), dict) or not index["weight_map"]:
        raise ModelResolutionError(f"safetensors index has no weight_map: {index_path}")
    shards = sorted(set(str(name) for name in index["weight_map"].values()))
    missing = [name for name in shards if not (root / name).is_file()]
    if missing:
        raise ModelResolutionError(f"missing safetensors shards under {root}: {missing}")
    return root


def find_model_candidates(role: ModelRole, input_root: Path) -> list[Path]:
    input_root = Path(input_root).expanduser().resolve()
    if not input_root.exists():
        return []
    candidates: list[Path] = []
    for index_path in input_root.rglob("model.safetensors.index.json"):
        root = index_path.parent
        try:
            candidates.append(validate_model_root(root, role))
        except ModelResolutionError:
            continue
    return sorted(set(candidates))


def resolve_model_path(
    role: ModelRole,
    explicit_path: str | None,
    input_root: Path | str = "/kaggle/input",
) -> Path:
    if explicit_path:
        return validate_model_root(Path(explicit_path), role)
    candidates = find_model_candidates(role, Path(input_root))
    if not candidates:
        raise ModelResolutionError(f"no validated {role} Qwen3-4B model found under {input_root}")
    if len(candidates) != 1:
        joined = "\n".join(f"- {item}" for item in candidates)
        raise ModelResolutionError(f"ambiguous {role} model discovery under {input_root}:\n{joined}")
    return candidates[0]
