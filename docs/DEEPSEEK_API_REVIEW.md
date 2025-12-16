# DeepSeek API — Review & Cline configuration

Summary
- DeepSeek exposes an OpenAI‑compatible API. Base URL: `https://api.deepseek.com` (you may also use `https://api.deepseek.com/v1` for OpenAI‑style SDKs; `/v1` is not a model version).
- Auth: Bearer token via `Authorization: Bearer <API_KEY>` header (same as OpenAI).
- Chat models: `deepseek-chat` (non‑thinking), `deepseek-reasoner` (thinking). There are also specialized models like `deepseek-coder:1.3b`.

Endpoints (OpenAI-compatible)
- Chat completions: `POST https://api.deepseek.com/chat/completions` (or `/v1/chat/completions` when using OpenAI SDKs with `base_url` set to `https://api.deepseek.com/v1`).
- The request/response shapes mirror OpenAI `chat/completions` (messages array, `model`, optional `stream`).

Behavior notes
- Set `stream: true` to receive streaming responses (the service supports streaming similar to OpenAI).
- The `v1` path is provided for compatibility with OpenAI SDKs; it does not imply model versioning.

Cline (VS Code extension) configuration mapping
- API Provider: select `OpenAI Compatible` in Cline UI.
- Base URL: `https://api.deepseek.com` (or `https://api.deepseek.com/v1` if Cline expects OpenAI base path).
- API Key: enter your DeepSeek API key in the extension's API key field or let Cline read it from environment/secret storage.
- Model ID: `deepseek-chat` or `deepseek-reasoner` (or `deepseek-coder:1.3b` for code tasks).
- If Cline provides a `Custom Headers` field, no extra header is necessary if it submits the key from the API Key box; otherwise add `Authorization: Bearer <YOUR_KEY>`.

Example requests

curl
```
export DEEPSEEK_API_KEY="<YOUR_KEY>"
curl https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"system","content":"You are helpful."},{"role":"user","content":"Hello"}],"stream":false}'
```

Python (OpenAI SDK compatible)
```
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role":"system","content":"You are helpful."},{"role":"user","content":"Hello"}],
    stream=False
)
print(resp.choices[0].message.content)
```

Notes & recommendations
- Do not store API keys in repository files. The repository previously had a DeepSeek key in `.vscode/settings.json`; it has been replaced with a placeholder.
- For Cline, prefer storing the key in VSCode's secure secrets or environment variables, and point the extension to use the OpenAI Compatible provider with the `base_url` above.
- If you hit 401s, confirm the header is `Authorization: Bearer <KEY>` and that the `base_url` is correct.
- If endpoints return unexpected errors, try switching between `https://api.deepseek.com` and `https://api.deepseek.com/v1` depending on how the client constructs the final path.

Model details (V3.2)

- Models / modes:
  - `deepseek-chat` — DeepSeek‑V3.2 (Non‑thinking Mode)
  - `deepseek-reasoner` — DeepSeek‑V3.2 (Thinking Mode)
  - `deepseek-reasoner(1)` — DeepSeek‑V3.2‑Speciale (Thinking Mode — Speciale)

- Context & output:
  - All models support large context windows (examples up to 128K depending on variant).
  - `deepseek-chat`: default max output 4K, maximum 8K.
  - `deepseek-reasoner`: default max output 32K, maximum 64K.
  - `deepseek-reasoner(1)` (Speciale): default max output 128K, maximum 128K.

- Features matrix (summary):
  - `deepseek-chat`: JSON Output ✓, Tool Calls ✓, Chat Prefix Completion (Beta) ✓, FIM Completion (Beta) ✓
  - `deepseek-reasoner`: JSON Output ✓, Tool Calls ✓, Chat Prefix Completion (Beta) ✓, FIM Completion ✗
  - `deepseek-reasoner(1)`: JSON Output ✗, Tool Calls ✗, Chat Prefix Completion ✗, FIM Completion ✗

- Pricing (doc examples):
  - 1M input tokens (cache hit): $0.028
  - 1M input tokens (cache miss): $0.28
  - 1M output tokens: $0.42

Expiration / special note:
- Some listings show `v3.2_speciale_expires_on_20251215` for the Speciale variant — confirm in the docs or with DeepSeek support if you rely on that variant for production.

References
- Official docs: https://api-docs.deepseek.com/

If you want, I can also:
- Add a short `README` with step‑by‑step Cline UI screenshots; or
- Create a small test script in `tools/` to validate the workspace's Cline settings against DeepSeek (uses environment variable for the key).

Cline quick configuration for DeepSeek V3.2

Use these exact UI values in the Cline model configuration panel when targeting DeepSeek V3.2 models.

- API Configuration
  - API Provider: `OpenAI Compatible`
  - Base URL: `https://api.deepseek.com` (If Cline auto-appends `/v1`, use `https://api.deepseek.com/v1` instead.)
  - OpenAI Compatible API Key: store in VSCode secret storage or set in the extension field (do NOT commit keys).

- Custom Headers (only if needed)
  - Header name: `Authorization`
  - Header value: `Bearer <YOUR_DEEPSEEK_API_KEY>`

- Model Configuration values (UI fields)
  - Context Window Size: `128000`
  - Max Output Tokens: set according to model:
    - `deepseek-chat`: use `4000` (up to `8000` max)
    - `deepseek-reasoner`: use `32000` (up to `64000` max)
    - `deepseek-reasoner(1)` (Speciale): use `128000`
  - Temperature: `0` (adjust as needed)
  - Supports Images: check if using multimodal features
  - Enable R1 messages format: leave unchecked unless you know the client requires it

- Advanced
  - If you want different models in Plan vs Act modes, enable `Use different models for Plan and Act modes` and configure each separately.

UI tip from screenshot: the panel shows `Context: 128K` and `Max Output Tokens` can be `-1` meaning no hard limit from the UI — prefer to set the documented maxima to avoid truncation.

Quick test checklist after saving settings
  - Confirm the extension sends `Authorization: Bearer <KEY>` (inspect DevTools network request).
  - If you get 404 errors, toggle the Base URL between `https://api.deepseek.com` and `https://api.deepseek.com/v1`.
  - If responses are truncated, reduce conversational history or increase `Max Output Tokens` to match model capability.

