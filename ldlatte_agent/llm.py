from __future__ import annotations

import json
import os
from typing import Protocol

import requests
from dotenv import load_dotenv


class JSONLLMClient(Protocol):
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1800,
    ) -> dict:
        ...


class DeepSeekClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 90,
    ) -> None:
        load_dotenv(override=False)
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL") or "deepseek-v4-flash"
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY не найден.")

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 1800,
    ) -> dict:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )
        if not response.ok:
            # Do not include headers or the API key in errors.
            raise RuntimeError(f"DeepSeek API error: HTTP {response.status_code}")
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("DeepSeek вернул невалидный JSON.") from exc
