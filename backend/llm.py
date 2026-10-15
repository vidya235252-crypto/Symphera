"""Real LLM call via Groq (OpenAI-compatible API). Signature is the contract with pipeline.py: analyze(text, language_hint) -> dict."""
import json
import os
import re
from pathlib import Path


class LLMError(Exception):
    pass


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
_SYSTEM = (Path(__file__).parent / "prompts" / "system.md").read_text(encoding="utf-8")


def _api_key() -> str:
    key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is not set")
    return key


def _build_user_message(text: str, language_hint: str) -> str:
    safe = re.sub(r"</?\s*user_input\s*>", "", text, flags=re.I)  # no tag breakout
    return f"language_hint: {language_hint}\n<user_input>\n{safe}\n</user_input>"


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
    temp = os.getenv("LLM_TEMPERATURE", "0.2")
    if temp:
        body["temperature"] = float(temp)
    if "gpt-oss" in MODEL:
        body["reasoning_effort"] = "low"  # keeps latency down on reasoning models

    try:
        r = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json=body,
            timeout=20.0,
        )
    except httpx.HTTPError as e:
        raise LLMError(f"network error: {e}") from e
    if r.status_code != 200:
        raise LLMError(f"Groq HTTP {r.status_code}: {r.text[:300]}")
    try:
        return r.json()["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"unexpected Groq response shape: {e}") from e


def _parse_json(raw: str) -> dict:
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("no JSON object in model output")
    try:
        obj = json.loads(s[start : end + 1])
    except json.JSONDecodeError as e:
        raise LLMError(f"invalid JSON from model: {e}") from e
    if not isinstance(obj, dict):
        raise LLMError("model output is not a JSON object")
    return obj


def analyze(text: str, language_hint: str = "auto") -> dict:
    return _parse_json(_call_model(_build_user_message(text, language_hint)))
