import json

import httpx
import pytest

from app.providers.ai_provider import AppealInput, ModerationInput
from app.providers.mimo_provider import MiMoProvider


def moderation_input() -> ModerationInput:
    return ModerationInput(
        content_id="content-1",
        author_id="user-1",
        author_name="张三",
        text="明天九点开始活动。",
        parent_text=None,
        topic_title="活动通知",
    )


def provider_for(content: str, status_code: int = 200):
    captured = {}

    def handler(request: httpx.Request):
        captured["request"] = json.loads(request.content)
        return httpx.Response(
            status_code,
            json={"choices": [{"message": {"content": content}}]} if status_code == 200 else {"error": "failed"},
        )

    return MiMoProvider(
        api_key="test-key",
        base_url="https://mimo.example/v1",
        model="mimo-test",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    ), captured


def test_mimo_moderation_parses_strict_json_and_sends_json_mode():
    output = {
        "isViolation": False,
        "riskLevel": 0,
        "riskScore": 3,
        "riskTypes": [],
        "confidence": 0.98,
        "decision": "publish",
        "targetUsers": [],
        "isQuoteOrReport": False,
        "quoteContextSafe": False,
        "hasImplicitAttack": False,
        "hasContinuousHarassment": False,
        "evidence": [],
        "contextReasoning": "未发现风险。",
        "userVisibleReason": "内容已发布。",
        "reviewerReason": "上下文安全。",
        "suggestedRevision": "",
        "intent": "通知活动时间",
        "contextUsed": ["当前内容"],
        "uncertainties": [],
    }
    provider, captured = provider_for(f"```json\n{json.dumps(output, ensure_ascii=False)}\n```")
    result = provider.moderate(moderation_input())
    assert result.decision == "publish"
    assert result.intent == "通知活动时间"
    assert captured["request"]["model"] == "mimo-test"
    assert captured["request"]["response_format"] == {"type": "json_object"}


def test_mimo_appeal_critic_uses_distinct_schema_and_prompt():
    output = {
        "supportsOriginalDecision": ["原文表面上像威胁。"],
        "supportsChange": ["补充说明这是引用台词。"],
        "newEvidenceImpact": "新上下文可能改变说话者意图判断。",
        "remainingUncertainties": [],
        "reviewSuggestion": "allow",
        "reviewerSummary": "建议人工核对引用来源。",
        "evidence": [
            {
                "contentId": "appeal-extra-context",
                "text": "引用台词",
                "reason": "说明内容不是现实威胁",
                "riskType": "counter_evidence",
            }
        ],
    }
    provider, captured = provider_for(json.dumps(output, ensure_ascii=False))
    result = provider.analyze_appeal(
        AppealInput(
            appeal_id="appeal-1",
            content=moderation_input(),
            appeal_type="missing_context",
            reason="初审遗漏上下文",
            extra_context="这是引用台词，不是现实威胁。",
            original_moderation={"systemDecision": "limit"},
        )
    )
    assert result.review_suggestion == "allow"
    sent = json.loads(captured["request"]["messages"][1]["content"])
    assert sent["task"] == "appeal_counter_analysis"
    assert sent["originalModeration"]["systemDecision"] == "limit"


def test_mimo_invalid_json_and_http_failure_are_visible_to_workflow():
    invalid_provider, _ = provider_for("not-json")
    with pytest.raises(json.JSONDecodeError):
        invalid_provider.moderate(moderation_input())

    failed_provider, _ = provider_for("", status_code=503)
    with pytest.raises(httpx.HTTPStatusError):
        failed_provider.moderate(moderation_input())
