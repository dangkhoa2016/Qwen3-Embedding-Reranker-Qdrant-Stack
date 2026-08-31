#!/usr/bin/env bash
set -Eeuo pipefail
set +x
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
: "${TORCHAO_VERSION:=0.18.0}"

python - <<'PY'
import torch
print(f"TORCH_BEFORE={torch.__version__}")
print(f"CUDA_AVAILABLE={torch.cuda.is_available()}")
PY
TORCH_BEFORE="$(python -c 'import torch; print(torch.__version__)')"

python -m pip install -q -r requirements.txt
python -m pip install -q --no-deps "torchao==${TORCHAO_VERSION}" --index-url https://download.pytorch.org/whl/cpu

TORCH_AFTER="$(python -c 'import torch; print(torch.__version__)')"
printf 'TORCH_BEFORE=%s\nTORCH_AFTER=%s\n' "$TORCH_BEFORE" "$TORCH_AFTER"
test "$TORCH_BEFORE" = "$TORCH_AFTER" || {
  echo 'FAIL: setup changed the preinstalled PyTorch version' >&2
  exit 31
}

PYTHONPATH="$ROOT/src" python - <<'PY'
import torch, transformers, torchao
from transformers import TorchAoConfig
from torchao.quantization import Int8DynamicActivationInt8WeightConfig, Int8WeightOnlyConfig
from qwen_dual_server.quantization import build_torchao_quantization_config
print("torch", torch.__version__)
print("transformers", transformers.__version__)
print("torchao", torchao.__version__)
for mode in ("int8-a8w8", "int8-weight-only"):
    cfg = build_torchao_quantization_config(mode)
    assert isinstance(cfg, TorchAoConfig)
    print(f"TORCHAO_CONFIG_{mode}=PASS")
PY

echo 'SETUP_INT8=PASS'
