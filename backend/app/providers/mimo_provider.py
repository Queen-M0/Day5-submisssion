import json
import re
from pathlib import Path
from typing import Any, Dict

import httpx

from app.providers.ai_provider import AppealInput, ModerationInput, ModerationProvider
from app.schemas.common import CounterAnalysisResult, ModerationResult


PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


class MiMoProvider(ModerationProvider):
    """MiMo adapter using its OpenAI-compatible chat-completions protocol."""

    name = "xiaomi-mimo"
    moderation_prompt_version = "moderation-v2"
    appeal_prompt_version = "appeal-critic-v1"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_tokens: int = 400,
        temperature: float = 0.1,
        json_mode: bool = True,
        client: httpx.Client | None = None,
    ):
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model_version = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.json_mode = json_mode
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def moderate(self, payload: ModerationInput) -> ModerationResult:
        raw = self._request_json(
            self._load_prompt("moderation-v2.md"),
            {"task": "moderation", "input": self._moderation_payload(payload)},
        )
        return ModerationResult.model_validate(raw)

    def analyze_appeal(self, payload: AppealInput) -> CounterAnalysisResult:
        raw = self._request_json(
            self._load_prompt("appeal-critic-v1.md"),
            {
                "task": "appeal_counter_analysis",
                "appealId": payload.appeal_id,
                "originalModeration": payload.original_moderation,
                "appeal": {
                    "type": payload.appeal_type,
                    "reason": payload.reason,
                    "extraContext": payload.extra_context,
                },
                "input": self._moderation_payload(payload.content),
            },
        )
        return CounterAnalysisResult.model_validate(raw)

    def _request_json(self, system_prompt: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("MIMO_API_KEY is not configured")
        body: Dict[str, Any] = {
            "model": self.model_version,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body,
        )
        response.raise_for_status()
        envelope = response.json()
        try:
            content = envelope["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("MiMo response does not contain choices[0].message.content") from exc
        if isinstance(content, list):
            content = "".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content)
        if not isinstance(content, str) or not content.strip():
            raise ValueError("MiMo returned empty content")
        cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content.strip(), flags=re.IGNORECASE)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("MiMo structured output must be a JSON object")
        return parsed

    @staticmethod
    def _load_prompt(name: str) -> str:
        return (PROMPT_DIR / name).read_text(encoding="utf-8")

    @staticmethod
    def _message_payload(message):
        return {
            "contentId": message.id,
            "authorId": message.author_id,
            "authorName": message.author_name,
            "text": message.text,
            "replyToContentId": message.parent_id,
        }

    def _moderation_payload(self, payload: ModerationInput) -> Dict[str, Any]:
        return {
            "currentContent": {
                "contentId": payload.content_id,
                "authorId": payload.author_id,
                "authorName": payload.author_name,
                "text": payload.text,
            },
            "topicTitle": payload.topic_title,
            "replyTo": None
            if not payload.parent_id
            else {
                "contentId": payload.parent_id,
                "authorId": payload.parent_author_id,
                "text": payload.parent_text,
            },
            "recentMessages": [self._message_payload(item) for item in payload.messages],
            "authorHistory": [self._message_payload(item) for item in payload.author_history],
            "targetUserHistory": [self._message_payload(item) for item in payload.target_history],
        }
