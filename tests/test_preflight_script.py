import json
import os
import subprocess
import sys
from pathlib import Path


def make_model(root: Path, role: str):
    root.mkdir(parents=True)
    (root/'config.json').write_text(json.dumps({'model_type':'qwen3','hidden_size':2560,'num_hidden_layers':36}))
    typ = 'sentence_transformers.models.Pooling' if role == 'embedding' else 'sentence_transformers.cross_encoder.modules.logit_score.LogitScore'
    (root/'modules.json').write_text(json.dumps([{'type':typ}]))
    (root/'tokenizer_config.json').write_text('{}')
    (root/'a.safetensors').write_bytes(b'x')
    (root/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'x':'a.safetensors'}}))


def test_preflight_discovers_both_roles_and_emits_json(tmp_path):
    make_model(tmp_path/'embedding', 'embedding')
    make_model(tmp_path/'reranker', 'reranker')
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'KAGGLE_INPUT_ROOT': str(tmp_path), 'PYTHONPATH': str(root/'src')}
    p = subprocess.run([sys.executable, str(root/'scripts/preflight.py')], env=env, text=True, capture_output=True)
    assert p.returncode == 0, p.stderr + p.stdout
    data = json.loads(p.stdout)
    assert data['models']['embedding'].endswith('/embedding')
    assert data['models']['reranker'].endswith('/reranker')
