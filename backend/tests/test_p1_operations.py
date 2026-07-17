from fastapi.testclient import TestClient

from app.main import app
from app.schemas.common import ModerationResult


REVIEWER_HEADERS = {"X-User-Id": "reviewer_1"}


def rule_payload(**overrides):
    value = {
        "name": "社区审核规则",
        "enabledRiskTypes": ["insult", "harassment", "threat", "fraud", "discrimination", "implicit_attack"],
        "autoLimitMinRiskLevel": 3,
        "manualReviewMinRiskLevel": 2,
        "minConfidence": 0.65,
        "requireGroundedEvidence": True,
        "routeDivergenceToManual": True,
        "changeReason": "P1 自动化测试更新规则",
    }
    value.update(overrides)
    return value


def test_login_token_and_protected_routes():
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/auth/me").status_code == 401
        assert anonymous.post("/api/auth/login", json={"username": "zhangsan", "password": "wrong-password"}).status_code == 401
        login = anonymous.post("/api/auth/login", json={"username": "zhangsan", "password": "user123"})
        assert login.status_code == 200
        token = login.json()["accessToken"]
        current = anonymous.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert current.status_code == 200
        assert current.json()["username"] == "zhangsan"
        forbidden = anonymous.get("/api/reviewer/statistics", headers={"Authorization": f"Bearer {token}"})
        assert forbidden.status_code == 403


def test_rule_configuration_is_versioned_and_auditable(client):
    current = client.get("/api/reviewer/rules", headers=REVIEWER_HEADERS)
    assert current.status_code == 200
    previous_version = current.json()["version"]
    updated = client.put("/api/reviewer/rules", headers=REVIEWER_HEADERS, json=rule_payload(minConfidence=0.99))
    assert updated.status_code == 200
    assert updated.json()["version"] != previous_version
    assert updated.json()["minConfidence"] == 0.99
    history = client.get("/api/reviewer/rules/history", headers=REVIEWER_HEADERS).json()["items"]
    assert len(history) >= 2
    assert sum(item["isActive"] for item in history) == 1
    assert client.get("/api/reviewer/rules", headers={"X-User-Id": "student_a"}).status_code == 403


def test_low_confidence_rule_routes_content_to_manual_review(client):
    created = client.post(
        "/api/topics/topic-campus-event/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "这是一条普通且没有风险的活动通知。"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["moderation"]["confidence"] == 0.96
    assert body["moderation"]["systemDecision"] == "manual_review"
    assert any("规则分流" in item for item in body["moderation"]["uncertainties"])
    restored = client.put("/api/reviewer/rules", headers=REVIEWER_HEADERS, json=rule_payload())
    assert restored.status_code == 200


def test_dual_model_divergence_is_saved_and_routed_to_manual(client, monkeypatch):
    from app.api.dependencies import moderation_service

    class SafeSecondary:
        name = "test-secondary"
        model_version = "secondary-test-v1"
        moderation_prompt_version = "moderation-test-v1"

        def moderate(self, _payload):
            return ModerationResult(
                is_violation=False,
                risk_level=0,
                risk_score=5,
                risk_types=[],
                confidence=0.95,
                decision="publish",
                context_reasoning="辅助模型判断为普通交流。",
                user_visible_reason="可以公开。",
                reviewer_reason="辅助模型未发现风险。",
            )

    monkeypatch.setattr(moderation_service, "secondary_provider", SafeSecondary())
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_b"},
        json={"text": "你放学等着，我会让你后悔。"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending_manual_review"
    assert body["moderation"]["dualReview"]["divergent"] is True
    assert body["moderation"]["dualReview"]["secondary"]["modelVersion"] == "secondary-test-v1"
    assert body["moderation"]["dualReview"]["systemResolution"] == "manual_review"


def test_statistics_endpoint_returns_all_p1_metrics(client):
    response = client.get("/api/reviewer/statistics", headers=REVIEWER_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert {
        "totalContents", "publicContents", "pendingManualReview", "limitedContents",
        "totalAppeals", "pendingAppeals", "appealApprovalRate", "manualReviews",
        "manualOverrides", "manualOverrideRate", "dualReviews", "dualDivergences", "dualDivergenceRate",
    }.issubset(body["summary"])
    assert len(body["riskLevelDistribution"]) == 4
    assert len(body["last7Days"]) == 7
    assert body["runtime"]["ruleVersion"].startswith("community-v")
