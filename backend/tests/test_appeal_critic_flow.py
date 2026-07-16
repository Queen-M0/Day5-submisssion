from app.api.dependencies import appeal_service
from app.schemas.common import AppealCriticResult, EvidenceItem


class _FakeCritic:
    """Deterministic appeal critic for offline tests."""

    name = "fake-appeal-critic"
    model_version = "fake-v1"
    prompt_version = "fake-appeal-v1"
    rule_version = "fake-community-v1"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.last_payload = None

    def critique(self, payload):
        self.last_payload = payload
        if self.error is not None:
            raise self.error
        return self.result


def _make_result(**overrides) -> AppealCriticResult:
    base = dict(
        upholds_initial=False,
        recommended_decision="overturn_allow",
        confidence=0.82,
        risk_level=3,
        risk_score=90,
        risk_types=["threat"],
        supports_original_decision=["初次审核判定为 threat，风险等级 3。"],
        supports_change=["申诉补充上下文说明是台词讨论，可能改变定性。"],
        new_evidence_impact="补充上下文可能说明该内容为台词而非真实威胁。",
        remaining_uncertainties=[],
        evidence=[],
        review_suggestion="建议改判允许，结合补充上下文重新判断。",
        reasoning="反证 Agent 认为补充上下文足以推翻原判。",
    )
    base.update(overrides)
    return AppealCriticResult(**base)


def test_appeal_critic_writes_counter_analysis(client, monkeypatch):
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。", "replyToContentId": "floor-102"},
    ).json()
    content_id = created["contentId"]

    fake = _FakeCritic(result=_make_result())
    monkeypatch.setattr(appeal_service, "critic", fake)

    appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={
            "appealType": "missing_context",
            "reason": "这句话缺少前文，请重新判断。",
            "extraContext": "这是对舞台剧台词的讨论，不是现实威胁。",
        },
    )
    assert appeal.status_code == 201
    body = appeal.json()
    assert body["aiAnalyzed"] is True
    assert body["status"] == "reviewing"
    counter = body["counterAnalysis"]
    assert counter is not None
    assert counter["provider"] == "fake-appeal-critic"
    assert counter["initialReviewId"]
    assert counter["supportsOriginalDecision"]
    assert counter["supportsChange"]
    assert counter["newEvidenceImpact"]
    assert counter["reviewSuggestion"]
    assert counter["upholdsInitial"] is False
    assert counter["recommendedDecision"] == "overturn_allow"

    # The counter analysis is persisted and surfaced on the reviewer task.
    task = client.get(
        f"/api/reviewer/tasks/appeal__{body['appealId']}", headers={"X-User-Id": "reviewer_1"}
    )
    assert task.status_code == 200
    assert task.json()["counterAnalysis"]["initialReviewId"] == counter["initialReviewId"]

    # And on the user's own appeal list.
    mine = client.get("/api/me/appeals", headers={"X-User-Id": "student_a"}).json()["items"]
    mine_counter = next(item for item in mine if item["id"] == body["appealId"])["counterAnalysis"]
    assert mine_counter["recommendedDecision"] == "overturn_allow"


def test_appeal_critic_consumes_initial_review(client, monkeypatch):
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。", "replyToContentId": "floor-102"},
    ).json()
    content_id = created["contentId"]
    assert created["status"] == "limited"  # initial review was a limit

    fake = _FakeCritic(result=_make_result())
    monkeypatch.setattr(appeal_service, "critic", fake)

    extra = "舞台剧台词，非真实威胁。"
    client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={"appealType": "misunderstanding", "reason": "请结合上文重新判断。", "extraContext": extra},
    )

    # The critic must have received the persisted initial review, time-decoupled.
    payload = fake.last_payload
    assert payload is not None
    assert payload.initial_review.system_decision == "limit"
    assert payload.initial_review.risk_types == ["threat"]
    assert payload.extra_context == extra
    assert payload.appeal_type == "misunderstanding"


def test_appeal_critic_evidence_cross_floor_validated(client, monkeypatch):
    # Reply to floor-103 so the critic can cite a real, different floor.
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。", "replyToContentId": "floor-103"},
    ).json()
    content_id = created["contentId"]

    captured = {}

    def build_result(payload):
        # Cite the first real context floor verbatim.
        floor = payload.context_messages[0]
        captured["id"] = floor.id
        captured["text"] = floor.text
        return _make_result(
            evidence=[EvidenceItem(text=floor.text, reason="引用其它楼层的原文作为反证", risk_type="context", content_id=floor.id)]
        )

    class _CaptureCritic(_FakeCritic):
        def critique(self, payload):
            self.last_payload = payload
            return build_result(payload)

    fake = _CaptureCritic()
    monkeypatch.setattr(appeal_service, "critic", fake)

    appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={"appealType": "missing_context", "reason": "请重新判断。", "extraContext": "引用了上文。"},
    ).json()
    counter = appeal["counterAnalysis"]
    assert counter is not None
    assert counter["evidence"]
    ev = counter["evidence"][0]
    assert ev["verified"] is True
    assert ev["contentId"] == captured["id"]
    assert ev["contentId"] != content_id  # evidence came from a *different* floor


def test_appeal_critic_failure_routes_to_manual(client, monkeypatch):
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。", "replyToContentId": "floor-102"},
    ).json()
    content_id = created["contentId"]

    fake = _FakeCritic(error=TimeoutError("mock timeout"))
    monkeypatch.setattr(appeal_service, "critic", fake)

    appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={"appealType": "missing_context", "reason": "请重新判断。", "extraContext": "x"},
    )
    assert appeal.status_code == 201
    body = appeal.json()
    # Failure path: no counter analysis, appeal stays in the manual queue.
    assert body["aiAnalyzed"] is False
    assert body["status"] == "submitted"
    assert body["counterAnalysis"] is None

    # Still reachable by a reviewer as a normal user_appeal task.
    task = client.get(
        f"/api/reviewer/tasks/appeal__{body['appealId']}", headers={"X-User-Id": "reviewer_1"}
    )
    assert task.status_code == 200
    assert task.json()["counterAnalysis"] is None
