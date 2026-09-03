#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

from qwen_dual_server.production_demo import locate_snapshot

FILENAME = "knowledge_entities_qwen3_4b_text_v21-20260827T013824Z.snapshot"
SIZE = 283812352
SHA256 = "71f12fe14ef51966069347290ad15302d389e488d7904dab6cf0cf190f43064f"

root = Path(os.environ.get("KAGGLE_INPUT_ROOT", "/kaggle/input"))
path = locate_snapshot(root, filename=FILENAME, expected_size=SIZE, expected_sha256=SHA256)
print(json.dumps({"path": str(path), "filename": FILENAME, "bytes": SIZE, "sha256": SHA256}, indent=2))
