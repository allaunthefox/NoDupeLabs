# AI / ONNX Runtime Backend — NoDupeLabs

This document explains the optional ONNX-based ML backend and CPU fallback we added for NSFW inference.

## Design goals
- Keep the core system working with **only standard library** dependencies.
- Provide optional GPU/ONNX paths that are **opt-in** and **gracefully degrade** when the runtime or model isn't present.
- Keep models outside the main runtime if they are large; prefer vendor-supplied artifacts or separate packaging.

## How it works
- `nodupe/ai/backends.py` exposes `choose_backend()` which attempts to instantiate an `ONNXBackend` (if `onnxruntime` is installed and a model file exists).
- If ONNX Runtime or the model is missing, a `CPUBackend` is returned — this is pure-Python and works in restricted environments.
- The `NSFWClassifier` now calls the chosen backend on image files as a TIER-3 analysis step; any errors in the backend are ignored and do not break scans.

## Configuration
In `nodupe.yml` you can customize AI settings:

```yaml
ai:
  enabled: auto            # auto|true|false — 'auto' will attempt to locate ONNX runtime & model
  backend: onnxruntime     # backend hint (currently: onnxruntime)
  model_path: models/nsfw_small.onnx
```

Notes:
- `ai.enabled: auto` will test runtime/model presence; set `false` to permanently disable ML inference.
- If you provide an ONNX model at `model_path`, the ONNX backend will be used when `onnxruntime` is installed and a matching execution provider (CUDA/ROCm/DirectML/CPU) exists.

## Testing
- Unit tests that exercise the AI backend and NSFW integration were added in `tests/test_ai_backend.py` and `tests/test_nsfw_integration.py`.
- CI runs on CPU-only environments and will exercise the CPU fallback path.

## Next steps (optional)
- Add a small onnx model as a separate release artifact or vendor a tiny demo under `nodupe/models/` (watch repo size).
- Optionally add FAISS for similarity search after you generate embeddings with the chosen ML backend.
