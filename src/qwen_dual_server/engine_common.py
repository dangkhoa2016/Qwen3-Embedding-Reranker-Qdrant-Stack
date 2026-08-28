from __future__ import annotations

from collections import Counter
from collections.abc import Collection

import torch


def resolve_torch_dtype(name: str) -> torch.dtype:
    mapping = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    try:
        return mapping[name]
    except KeyError as exc:
        raise ValueError(f"unsupported model dtype: {name}") from exc


def select_dtype_keyword(parameter_names: Collection[str]) -> str:
    names = set(parameter_names)
    if "dtype" in names:
        return "dtype"
    if "torch_dtype" in names:
        return "torch_dtype"
    raise RuntimeError(
        "Transformers PreTrainedModel.from_pretrained exposes neither "
        "'dtype' nor legacy 'torch_dtype'"
    )


def current_transformers_dtype_keyword() -> str:
    """Pick the truthful dtype keyword for the installed Transformers.

    Transformers >=4.54 renamed `torch_dtype` to `dtype` and routes it through
    **kwargs, so a signature-name lookup cannot see it. Verify the installed
    source behavior directly instead of hard-coding a version cutoff.
    """
    try:
        import inspect

        from transformers import PreTrainedModel
    except ImportError:
        return "torch_dtype"
    parameters = inspect.signature(PreTrainedModel.from_pretrained).parameters
    if "dtype" in parameters:
        return "dtype"
    if "torch_dtype" in parameters:
        return "torch_dtype"
    if 'kwargs.pop("dtype", None)' in inspect.getsource(PreTrainedModel.from_pretrained):
        return "dtype"
    return "torch_dtype"


def model_dtype_kwargs(torch_dtype) -> dict[str, object]:
    return {current_transformers_dtype_keyword(): torch_dtype}


def validate_model_cpu_dtype(model, expected_dtype: torch.dtype) -> dict[str, object]:
    dtype_bytes: Counter[str] = Counter()
    devices: set[str] = set()
    parameter_count = 0
    for param in model.parameters():
        parameter_count += int(param.numel())
        devices.add(str(param.device))
        if param.is_floating_point():
            dtype_bytes[str(param.dtype)] += int(param.numel() * param.element_size())
    if not devices:
        raise RuntimeError("loaded model has no parameters")
    if any(device != "cpu" for device in devices):
        raise RuntimeError(f"CPU-only contract violated; observed parameter devices={sorted(devices)}")
    observed = set(dtype_bytes)
    expected_name = str(expected_dtype)
    if observed != {expected_name}:
        raise RuntimeError(
            f"model dtype contract violated; expected only {expected_name}, observed={dict(dtype_bytes)}"
        )
    return {
        "parameter_count": parameter_count,
        "parameter_devices": sorted(devices),
        "floating_parameter_bytes_by_dtype": dict(dtype_bytes),
    }
