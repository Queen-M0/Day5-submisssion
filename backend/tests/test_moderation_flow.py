def test_safe_quote_is_published(client):
    response = client.post(
        "/api/contents",
        headers={"X-User-Id": "student_a"},
        json={
            "sceneId": "campus_forum_001",
            "contentType": "forum_reply",
            "parentId": "seed_001",
            "text": "楼上说“你就是废物”这种话不合适，请管理员处理。",
        },
    )
    assert response.status_code == 201
    assert response.json()["decision"] == "publish"
    assert response.json()["riskLevel"] == 0


def test_high_risk_content_can_be_appealed_and_reviewed(client):
    created = client.post(
        "/api/contents",
        headers={"X-User-Id": "student_a"},
        json={
            "sceneId": "campus_forum_001",
            "contentType": "forum_reply",
            "text": "你放学等着，我会让你后悔。",
        },
    )
    assert created.status_code == 201
    assert created.json()["status"] == "limited"
    content_id = created.json()["contentId"]

    appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={"appealType": "missing_context", "reason": "这句话缺少前文，请人工重新判断。"},
    )
    assert appeal.status_code == 201
    appeal_id = appeal.json()["appealId"]

    decision = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={
            "finalDecision": "publish",
            "finalRiskLevel": 0,
            "reviewReason": "结合补充上下文，确认不构成真实威胁。",
            "correctionType": "false_positive_context",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["contentStatus"] == "published"
    assert decision.json()["appealStatus"] == "approved"


def test_implicit_attack_enters_manual_queue(client):
    response = client.post(
        "/api/contents",
        headers={"X-User-Id": "student_b"},
        json={
            "sceneId": "campus_forum_001",
            "contentType": "forum_reply",
            "parentId": "seed_002",
            "text": "别让那个“大聪明”碰展示，懂的都懂。",
        },
    )
    assert response.status_code == 201
    assert response.json()["decision"] == "manual_review"
    assert response.json()["status"] == "pending_manual_review"
