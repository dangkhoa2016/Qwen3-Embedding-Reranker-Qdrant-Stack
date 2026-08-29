import torch

from qwen_dual_server.tensor_ops import last_token_pool, normalize_embedding_fp32


def test_last_token_pool_left_padding_uses_final_position():
    states = torch.tensor([
        [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]],
        [[4.0, 4.0], [5.0, 5.0], [6.0, 6.0]],
    ])
    mask = torch.tensor([[0, 1, 1], [1, 1, 1]])
    pooled = last_token_pool(states, mask)
    assert torch.equal(pooled, torch.tensor([[3.0, 3.0], [6.0, 6.0]]))


def test_last_token_pool_right_padding_uses_last_unmasked_position():
    states = torch.tensor([
        [[1.0, 0.0], [2.0, 0.0], [99.0, 99.0]],
        [[4.0, 0.0], [5.0, 0.0], [6.0, 0.0]],
    ])
    mask = torch.tensor([[1, 1, 0], [1, 1, 1]])
    pooled = last_token_pool(states, mask)
    assert torch.equal(pooled, torch.tensor([[2.0, 0.0], [6.0, 0.0]]))


def test_normalization_casts_to_float32_before_l2_normalize():
    source = torch.tensor([[3.0, 4.0]], dtype=torch.float16)
    out = normalize_embedding_fp32(source)
    assert out.dtype == torch.float32
    assert torch.allclose(out, torch.tensor([[0.6, 0.8]], dtype=torch.float32), atol=1e-6)
    assert torch.allclose(torch.linalg.vector_norm(out, dim=1), torch.ones(1), atol=1e-6)
