# DeepSeek V3.2 — Setup & Cline configuration

This note summarizes the official guidance for using DeepSeek V3.2 models (from https://api-docs.deepseek.com/) and how to configure the Cline (VS Code) extension to call them.

What V3.2 provides
- DeepSeek‑V3.2 is available via several model IDs:
  - `deepseek-chat` — the non‑thinking / standard chat mode for V3.2
  - `deepseek-reasoner` — the reasoning/thinking mode of V3.2 (for agent‑style reasoning)
  - `deepseek-coder:1.3b` — a specialized code model (example)

Base URL & compatibility
- Base URL: `https://api.deepseek.com` (or `https://api.deepseek.com/v1` to use OpenAI SDKs). The `v1` path is purely for OpenAI API shape compatibility and does not indicate model versioning.
- The API is OpenAI‑compatible for the common endpoints (chat/completions, streaming, etc.). Use the same request shapes as OpenAI's chat completions.

Authentication
- Use Bearer auth: send header `Authorization: Bearer <DEEPSEEK_API_KEY>` or enter the key in a client/extension field that will add the header for you.

Cline (VS Code) recommended settings
- Open the Cline extension settings.
- API Provider: choose `OpenAI Compatible`.
- Base URL: `https://api.deepseek.com` (if Cline constructs paths like `/v1/...` you may instead set `https://api.deepseek.com/v1`).
- API Key: store your key in secure storage or environment and point Cline to use it.
- Model ID: pick `deepseek-chat` or `deepseek-reasoner` depending on whether you want normal chat vs reasoning mode; use `deepseek-coder:1.3b` for code assistance.
- Streaming: enable streaming in Cline if you want progressive output (the API supports `stream: true`).

Examples

curl
```
export DEEPSEEK_API_KEY="<YOUR_KEY>"
curl https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-reasoner","messages":[{"role":"system","content":"You are a careful reasoner."},{"role":"user","content":"Explain recursion."}],"stream":false}'
```

Python (OpenAI SDK compatible)
```
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

resp = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role":"system","content":"You are a careful reasoner."},
              {"role":"user","content":"Explain recursion."}],
    stream=False
)
print(resp.choices[0].message.content)
```

Notes & best practices for V3.2
- Choose `deepseek-reasoner` when you need multi-step reasoning, chain-of-thought, or agent-like behavior. Use `deepseek-chat` for typical conversational tasks (faster, less introspective).
- For coding tasks prefer `deepseek-coder:1.3b` or whatever the docs list as the latest code model.
- Use streaming (`stream: true`) for interactive UX in editors/IDE extensions.
- If an SDK or client assumes OpenAI's host/path style, set `base_url` to include `/v1` to avoid double-pathing issues.

Troubleshooting
- 401 Unauthorized: verify key, ensure `Authorization: Bearer <KEY>` header is sent.
- Unexpected 404/endpoint errors: try alternate base URL (`/v1` vs root) depending on how the client concatenates paths.
- Non‑streaming when requested: ensure client supports SSE / streaming and Cline is configured to accept streamed chunks.

References
- DeepSeek API docs: https://api-docs.deepseek.com/

Model details (V3.2)

- Models and modes:
  - `deepseek-chat` — DeepSeek‑V3.2 (Non‑thinking mode)
  - `deepseek-reasoner` — DeepSeek‑V3.2 (Thinking mode)
  - `deepseek-reasoner(1)` — DeepSeek‑V3.2‑Speciale (Thinking mode only; special variant)
  - `deepseek-coder:1.3b` — code-specialized model (example)

- Base URL per model listing:
  - `https://api.deepseek.com` or `https://api.deepseek.com/` (both accepted)

- Context & output limits:
  - `deepseek-chat`: Context length 128K; Max output default 4K, maximum 8K.
  - `deepseek-reasoner`: Context length 128K; Max output default 32K, maximum 64K.
  - `deepseek-reasoner(1)` (Speciale): Context length 128K; Max output default 128K, maximum 128K.

- Features by model:
  - `deepseek-chat`: Json Output ✓, Tool Calls ✓, Chat Prefix Completion (Beta) ✓, FIM Completion (Beta) ✓
  - `deepseek-reasoner`: Json Output ✓, Tool Calls ✓, Chat Prefix Completion (Beta) ✓, FIM Completion ✗
  - `deepseek-reasoner(1)` (Speciale): Json Output ✗, Tool Calls ✗, Chat Prefix Completion ✗, FIM Completion ✗

- Special notes:
  - The `deepseek-reasoner(1)` entry may be labelled `v3.2_speciale_expires_on_20251215` in some listings — check the docs for deprecation/expiry info.

Pricing (examples from docs)
- Input tokens (per 1M): cache hit $0.028, cache miss $0.28
- Output tokens (per 1M): $0.42

