#!/usr/bin/env python3
"""Simple DeepSeek V3.2 chat/completions smoke test.

Usage:
  export DEEPSEEK_API_KEY="<YOUR_KEY>"
  export DEEPSEEK_MODEL="deepseek-chat"  # or deepseek-reasoner
  python3 tools/deepseek_test.py

This script uses plain HTTP so it doesn't depend on OpenAI SDKs.
"""
import os
import sys
import json
import requests


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: set DEEPSEEK_API_KEY in your environment.")
        sys.exit(2)

    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    url = base.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello and report your model id and max context if available."},
        ],
        "stream": False,
    }

    print(f"POST {url} (model={model})")
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)

    try:
        r.raise_for_status()
    except Exception as e:
        print("Request failed:", e)
        print("Status:", r.status_code)
        print(r.text)
        sys.exit(1)

    try:
        data = r.json()
    except Exception:
        print("Non-json response:")
        print(r.text)
        sys.exit(1)

    # best-effort output display
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        # both OpenAI and DeepSeek use nested message content
        msg = choice.get("message") or choice.get("text") or {}
        if isinstance(msg, dict):
            print("--- assistant message ---")
            print(msg.get("content"))
        else:
            print("--- assistant output ---")
            print(msg)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
