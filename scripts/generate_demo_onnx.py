"""Generate a tiny ONNX demo model used by NoDupeLabs for ML backend smoke tests.

This script will attempt to create `nodupe/models/nsfw_small.onnx`. It requires `onnx` package.
"""
from pathlib import Path

try:
    import onnx
    from onnx import helper, TensorProto
    import numpy as np
except Exception as e:
    print("Required packages for generating the ONNX demo model are not available:", e)
    print("Install onnx (and numpy) and re-run: python scripts/generate_demo_onnx.py")
    raise SystemExit(1)

p = Path(__file__).parent.parent / 'nodupe' / 'models'
p.mkdir(parents=True, exist_ok=True)

# Build a tiny model: input -> GlobalAveragePool -> Flatten -> Gemm to single output
input_tensor = helper.make_tensor_value_info('input', TensorProto.FLOAT, ['N', 3, 32, 32])
output_tensor = helper.make_tensor_value_info('output', TensorProto.FLOAT, ['N', 1])

pool_node = helper.make_node('GlobalAveragePool', ['input'], ['pooled'], name='global_pool')
flatten_node = helper.make_node('Flatten', ['pooled'], ['flat'], name='flatten', axis=1)

weights = np.random.RandomState(1).randn(1, 3).astype('float32')
bias = np.random.RandomState(2).randn(1).astype('float32')

W_init = helper.make_tensor('W', TensorProto.FLOAT, dims=weights.shape, vals=weights.flatten().tolist())
b_init = helper.make_tensor('b', TensorProto.FLOAT, dims=bias.shape, vals=bias.flatten().tolist())

gemm_node = helper.make_node('Gemm', ['flat', 'W', 'b'], ['output'], name='fc')

graph = helper.make_graph([pool_node, flatten_node, gemm_node], 'nsfw_small_graph', [input_tensor], [output_tensor], initializer=[W_init, b_init])

model = helper.make_model(graph, producer_name='nodupe-demo')

out_path = p / 'nsfw_small.onnx'
onnx.save(model, str(out_path))
print('Saved model to', out_path)
