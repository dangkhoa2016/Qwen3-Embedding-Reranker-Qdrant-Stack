from __future__ import annotations

from collections import Counter
from typing import Literal

import torch

QuantizationMode = Literal["none", "int8-a8w8", "int8-weight-only"]


def build_torchao_quantization_config(
    mode: QuantizationMode,
    *,
    torchao_config_cls=None,
    a8w8_cls=None,
    weight_only_cls=None,
):
    """Build a Transformers TorchAoConfig lazily.

    Imports are delayed so the frozen FP16 path remains usable without torchao.
    """
    if mode == "none":
        return None
    if torchao_config_cls is None or a8w8_cls is None or weight_only_cls is None:
        try:
            from transformers import TorchAoConfig
            from torchao.quantization import (
                Int8DynamicActivationInt8WeightConfig,
                Int8WeightOnlyConfig,
            )
        except Exception as exc:  # fail closed with actionable context
            raise RuntimeError(
                "TorchAO INT8 requested but transformers/torchao integration is unavailable: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        torchao_config_cls = TorchAoConfig
        a8w8_cls = Int8DynamicActivationInt8WeightConfig
        weight_only_cls = Int8WeightOnlyConfig

    if mode == "int8-a8w8":
        quant_type = a8w8_cls()
    elif mode == "int8-weight-only":
        quant_type = weight_only_cls()
    else:
        raise ValueError(f"unsupported quantization mode: {mode}")
    return torchao_config_cls(quant_type=quant_type)


def quantized_model_load_kwargs(mode: QuantizationMode) -> dict[str, object]:
    if mode == "none":
        return {}
    return {
        "dtype": "auto",
        "device_map": "cpu",
        "quantization_config": build_torchao_quantization_config(mode),
    }


def _looks_like_torchao_quantized_weight(weight) -> bool:
    cls = type(weight)
    module = getattr(cls, "__module__", "").lower()
    name = getattr(cls, "__name__", "").lower()
    markers = ("torchao", "affinequantized", "quantizedtensor", "int8tensor", "linearactivationquantized")
    return any(marker in module or marker in name for marker in markers)


def validate_quantized_cpu_model(model, mode: QuantizationMode) -> dict[str, object]:
    """Prove CPU residency and that TorchAO actually materialized quantized weights.

    Unlike the frozen FP16 validator, mixed residual floating dtypes are expected.
    """
    if mode == "none":
        raise ValueError("quantized model validation requires an INT8 mode")

    devices: set[str] = set()
    parameter_count = 0
    parameter_bytes = 0
    dtype_bytes: Counter[str] = Counter()
    for param in model.parameters():
        parameter_count += int(param.numel())
        parameter_bytes += int(param.numel() * param.element_size())
        devices.add(str(param.device))
        dtype_bytes[str(param.dtype)] += int(param.numel() * param.element_size())

    if not devices:
        raise RuntimeError("loaded model has no parameters")
    if any(device != "cpu" for device in devices):
        raise RuntimeError(f"CPU-only contract violated; observed parameter devices={sorted(devices)}")

    quantized_weight_modules = 0
    quantized_weight_types: Counter[str] = Counter()
    named_modules = getattr(model, "named_modules", None)
    if callable(named_modules):
        for _, module in named_modules():
            weight = getattr(module, "weight", None)
            if weight is not None and _looks_like_torchao_quantized_weight(weight):
                quantized_weight_modules += 1
                cls = type(weight)
                quantized_weight_types[f"{cls.__module__}.{cls.__name__}"] += 1

    if quantized_weight_modules == 0:
        raise RuntimeError(
            "TorchAO INT8 was requested but no TorchAO quantized weight tensor was observed; "
            "refusing to label the model INT8"
        )

    return {
        "quantization_mode": mode,
        "parameter_count": parameter_count,
        "parameter_devices": sorted(devices),
        "parameter_storage_bytes_visible": parameter_bytes,
        "parameter_bytes_by_dtype_visible": dict(dtype_bytes),
        "quantized_weight_modules": quantized_weight_modules,
        "quantized_weight_types": dict(quantized_weight_types),
    }
