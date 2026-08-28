import torch
import torch.nn.functional as F
from torch import Tensor


def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    left_padding = bool((attention_mask[:, -1].sum() == attention_mask.shape[0]).item())
    if left_padding:
        return last_hidden_states[:, -1]
    sequence_lengths = attention_mask.sum(dim=1) - 1
    batch_size = last_hidden_states.shape[0]
    rows = torch.arange(batch_size, device=last_hidden_states.device)
    return last_hidden_states[rows, sequence_lengths]


def normalize_embedding_fp32(pooled: Tensor) -> Tensor:
    return F.normalize(pooled.float(), p=2, dim=1)
