#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qwen_dual_server.memory import capture_memory_snapshot  # noqa: E402
from qwen_dual_server.model_locator import find_model_candidates, validate_model_root  # noqa: E402


def main() -> int:
    import torch
    root = Path(os.getenv("KAGGLE_INPUT_ROOT", "/kaggle/input"))
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cpu_count": psutil.cpu_count(logical=True),
        "memory": capture_memory_snapshot().to_dict(),
        "input_root": str(root),
        "models": {},
    }
    ok = True
    for role, env_name in (("embedding", "EMBEDDING_MODEL_PATH"), ("reranker", "RERANKER_MODEL_PATH")):
        explicit = os.getenv(env_name)
        try:
            if explicit:
                meta = validate_model_root(Path(explicit), role)
                candidates = [meta]
            else:
                candidates = find_model_candidates(role, root)
                if len(candidates) != 1:
                    raise RuntimeError(f"expected exactly one {role} model candidate, found {len(candidates)}")
            report["models"][role] = str(candidates[0])
        except Exception as exc:
            report["models"][role] = {"error": f"{type(exc).__name__}: {exc}"}
            ok = False
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
