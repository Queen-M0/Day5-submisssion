import json
from typing import Any, Dict


import httpx


def call_openai_json(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 12.0,
    temperature: float = 0.0,
    max_tokens: int = 900,
) -> Dict[str, Any]:
    """Call an OpenAI-compatible chat API and return the parsed JSON object.

    Raises httpx.HTTPStatusError on bad HTTP status and ValueError when the
    response shape is unexpected or the content is not valid JSON. The caller
    (service layer) turns these into a deterministic "route to manual review"
    outcome.
    """
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"unexpected chat completion shape: {exc}") from exc

    return _parse_json(content)


def _parse_json(content: str) -> Dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text[:4].lower() == "json":
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
