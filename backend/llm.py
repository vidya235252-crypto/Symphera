"""Real LLM call via Groq (OpenAI-compatible API).

Contract with pipeline.py:
    analyze(text, language_hint) -> dict
"""

import json
import os
import re
from pathlib import Path

import sources


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

_SYSTEM = (
    (Path(__file__).parent / "prompts" / "system.md")
    .read_text(encoding="utf-8")
    .replace("{{SOURCES}}", sources.render_for_prompt())
)


class LLMError(Exception):
    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


def _api_key() -> str:
    key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set")
    return key


def _build_user_message(
    text: str,
    language_hint: str,
    reminder: str = "",
) -> str:
    safe = re.sub(r"</?\s*user_input\s*>", "", text, flags=re.I)
    message = f"language_hint: {language_hint}\n<user_input>\n{safe}\n</user_input>"
    return f"{message}\n\n{reminder}" if reminder else message


def _call_model(user_message: str) -> str:
    import httpx

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "response_format": {"type": "json_object"},
        "max_completion_tokens": 2500,
    }

    temperature = os.getenv("LLM_TEMPERATURE", "0.2")
    if temperature:
        body["temperature"] = float(temperature)

    if "gpt-oss" in MODEL:
        body["reasoning_effort"] = "low"

    try:
        response = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json=body,
            timeout=20.0,
        )
    except httpx.HTTPError as exc:
        raise LLMError(f"network error: {exc}") from exc

    if response.status_code != 200:
        raise LLMError(
            f"Groq HTTP {response.status_code}: {response.text[:300]}",
            raw_output=response.text,
        )

    try:
        payload = response.json()
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError(
            f"unexpected Groq response shape: {exc}",
            raw_output=response.text,
        ) from exc


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw.strip(),
        flags=re.I,
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end <= start:
        raise LLMError("no JSON object in model output", raw_output=raw)

    try:
        result = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(
            f"invalid JSON from model: {exc}",
            raw_output=raw,
        ) from exc

    if not isinstance(result, dict):
        raise LLMError(
            "model output is not a JSON object",
            raw_output=raw,
        )

    return result


def analyze(
    text: str,
    language_hint: str = "auto",
    reminder: str = "",
) -> dict:
    user_message = _build_user_message(text, language_hint, reminder)
    raw = _call_model(user_message)
    return _parse_json(raw)