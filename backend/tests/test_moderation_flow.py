def test_community_and_public_topics_match_contract(client):
    community = client.get("/api/community").json()
    assert community["id"] == "community-001"
    assert community["topicCount"] == 3
    assert community["publicFloorCount"] == 7
    assert community["memberCount"] == 3

    topics = client.get("/api/topics?category=训练营协作&q=团队赛").json()["items"]
    assert len(topics) == 1
    assert topics[0]["id"] == "topic-ai-camp"
    assert topics[0]["publicFloorCount"] == 3


def test_safe_quote_is_published_with_next_floor_number(client):
    response = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={
            "replyToContentId": "floor-103",
            "text": "楼上说“你就是废物”这种话不合适，请管理员处理。",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "published"
    assert body["floorNumber"] == 4
    assert body["moderation"]["suggestedAction"] == "allow"
    assert body["moderation"]["systemDecision"] == "publish"


def test_private_contents_are_only_visible_to_author_and_reviewer(client):
    other_user_items = client.get(
        "/api/topics/topic-ai-camp/contents", headers={"X-User-Id": "student_c"}
    ).json()["items"]
    assert "floor-quote" not in {item["id"] for item in other_user_items}
    assert "floor-harassment" not in {item["id"] for item in other_user_items}

    author_items = client.get(
        "/api/topics/topic-ai-camp/contents", headers={"X-User-Id": "student_a"}
    ).json()["items"]
    assert "floor-quote" in {item["id"] for item in author_items}
    assert "floor-harassment" not in {item["id"] for item in author_items}

    reviewer_items = client.get(
        "/api/topics/topic-ai-camp/contents", headers={"X-User-Id": "reviewer_1"}
    ).json()["items"]
    assert {"floor-quote", "floor-harassment"}.issubset({item["id"] for item in reviewer_items})


def test_high_risk_content_can_be_appealed_and_restored(client):
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。", "replyToContentId": "floor-102"},
    )
    assert created.status_code == 201
    created_body = created.json()
    assert created_body["status"] == "limited"
    assert created_body["floorNumber"] is None
    content_id = created_body["contentId"]

    hidden = client.get(
        "/api/topics/topic-ai-camp/contents", headers={"X-User-Id": "student_c"}
    ).json()["items"]
    assert content_id not in {item["id"] for item in hidden}

    appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={
            "appealType": "missing_context",
            "reason": "这句话缺少前文，请人工重新判断。",
            "extraContext": "这是对舞台剧台词的讨论，不是现实威胁。",
        },
    )
    assert appeal.status_code == 201
    appeal_id = appeal.json()["appealId"]

    task = client.get(
        f"/api/reviewer/tasks/appeal__{appeal_id}", headers={"X-User-Id": "reviewer_1"}
    )
    assert task.status_code == 200
    counter = task.json()["counterAnalysis"]
    assert counter is not None
    assert "supportsOriginalDecision" in counter
    assert "supportsChange" in counter
    assert "newEvidenceImpact" in counter
    assert "reviewSuggestion" in counter
    assert counter["provider"] == "mock-appeal-critic"
    assert task.json()["appeal"]["extraContext"].startswith("这是对舞台剧")

    decision = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={
            "finalDecision": "allow",
            "reviewReason": "结合补充上下文，确认这段内容属于台词讨论，不构成真实威胁。",
        },
    )
    assert decision.status_code == 200
    result = decision.json()
    assert result["contentStatus"] == "appeal_approved"
    assert result["appealStatus"] == "approved"
    assert result["visibleToPublic"] is True
    assert result["floorNumber"] is not None

    duplicate = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={"finalDecision": "allow", "reviewReason": "重复提交应当被拒绝。"},
    )
    assert duplicate.status_code == 409

    timeline = client.get(
        f"/api/contents/{content_id}/timeline", headers={"X-User-Id": "student_a"}
    ).json()["items"]
    assert "manual_review.decided" in {event["action"] for event in timeline}
    assert "content.restored" in {event["action"] for event in timeline}


def test_implicit_attack_enters_manual_queue_and_history(client):
    response = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_b"},
        json={
            "replyToContentId": "floor-103",
            "text": "别让那个“大聪明”碰展示，懂的都懂。",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_manual_review"
    assert body["floorNumber"] is None

    task_id = f"content__{body['contentId']}"
    pending = client.get(
        "/api/reviewer/tasks?status=pending&source=ai_escalation",
        headers={"X-User-Id": "reviewer_1"},
    ).json()["items"]
    assert task_id in {item["taskId"] for item in pending}

    decision = client.post(
        f"/api/reviewer/tasks/{task_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={
            "finalDecision": "maintain_limit",
            "reviewReason": "结合回复对象和连续表达，维持限制处理。",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["contentStatus"] == "limited"

    history = client.get(
        "/api/reviewer/tasks?status=resolved&source=ai_escalation",
        headers={"X-User-Id": "reviewer_1"},
    ).json()["items"]
    assert task_id in {item["taskId"] for item in history}


def test_create_topic_keeps_root_private_until_approved(client):
    created = client.post(
        "/api/topics",
        headers={"X-User-Id": "student_c"},
        json={
            "title": "新的协作话题",
            "category": "训练营协作",
            "body": "先确认需求边界，再开始接口联调。",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "published"
    assert body["floorNumber"] == 1
    detail = client.get(
        f"/api/topics/{body['topicId']}", headers={"X-User-Id": "student_a"}
    )
    assert detail.status_code == 200
    assert detail.json()["visibleToPublic"] is True


def test_limited_topic_is_hidden_from_other_users(client):
    created = client.post(
        "/api/topics",
        headers={"X-User-Id": "student_c"},
        json={
            "title": "需要审核的话题",
            "category": "校园活动",
            "body": "你放学等着，我会让你后悔。",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "limited"
    assert body["floorNumber"] is None

    other_detail = client.get(
        f"/api/topics/{body['topicId']}", headers={"X-User-Id": "student_a"}
    )
    assert other_detail.status_code == 404
    owner_detail = client.get(
        f"/api/topics/{body['topicId']}", headers={"X-User-Id": "student_c"}
    )
    assert owner_detail.status_code == 200
    assert owner_detail.json()["visibleToPublic"] is False
    blocked_reply = client.post(
        f"/api/topics/{body['topicId']}/contents",
        headers={"X-User-Id": "student_c"},
        json={"text": "隐藏话题不能继续追加楼层。"},
    )
    assert blocked_reply.status_code == 409


def test_appeal_and_review_permissions_are_enforced(client):
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "你放学等着，我会让你后悔。"},
    ).json()
    content_id = created["contentId"]

    forbidden_appeal = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_b"},
        json={"reason": "我不是作者，不能替别人提交申诉。"},
    )
    assert forbidden_appeal.status_code == 403

    appeal_id = client.post(
        f"/api/contents/{content_id}/appeals",
        headers={"X-User-Id": "student_a"},
        json={"reason": "请结合完整上下文重新进行人工判断。"},
    ).json()["appealId"]
    forbidden_review = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "student_a"},
        json={"finalDecision": "allow", "reviewReason": "普通用户不能执行人工终审。"},
    )
    assert forbidden_review.status_code == 403

    old_enum = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={"finalDecision": "publish", "reviewReason": "旧枚举必须被校验拒绝。"},
    )
    assert old_enum.status_code == 422

    blank_reason = client.post(
        f"/api/reviewer/tasks/appeal__{appeal_id}/decision",
        headers={"X-User-Id": "reviewer_1"},
        json={"finalDecision": "allow", "reviewReason": "     "},
    )
    assert blank_reason.status_code == 422


def test_evidence_quote_from_other_floor_is_verified(client, monkeypatch):
    from app.api.dependencies import moderation_service
    from app.schemas.common import EvidenceItem, ModerationResult

    def moderate(payload):
        quoted = payload.messages[0] if payload.messages else None
        return ModerationResult(
            is_violation=True,
            risk_level=3,
            risk_score=88,
            risk_types=["insult"],
            confidence=0.9,
            decision="limit",
            evidence=[
                EvidenceItem(
                    text=quoted.text,
                    reason="引用了其它楼层的原文作为证据",
                    risk_type="insult",
                    content_id=quoted.id,
                )
            ],
            context_reasoning="证据来自上下文其它楼层。",
            user_visible_reason="内容已限制。",
            reviewer_reason="跨楼层证据校验。",
        )

    monkeypatch.setattr(moderation_service.provider, "moderate", moderate)
    created = client.post(
        "/api/topics/topic-ai-camp/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "这条内容引用楼上原话作为证据。", "replyToContentId": "floor-103"},
    )
    assert created.status_code == 201
    content_id = created.json()["contentId"]

    detail = client.get(
        f"/api/contents/{content_id}/moderation", headers={"X-User-Id": "reviewer_1"}
    ).json()
    assert detail["evidenceValid"] is True
    assert detail["evidence"][0]["verified"] is True
    assert detail["evidence"][0]["contentId"] != content_id


def test_fabricated_quote_fails_evidence_and_goes_manual(client, monkeypatch):
    from app.api.dependencies import moderation_service
    from app.schemas.common import EvidenceItem, ModerationResult

    def moderate(payload):
        return ModerationResult(
            is_violation=True,
            risk_level=3,
            risk_score=95,
            risk_types=["threat"],
            confidence=0.9,
            decision="limit",
            evidence=[
                EvidenceItem(
                    text="这段原文在任何楼层都不存在",
                    reason="编造的证据",
                    risk_type="threat",
                )
            ],
            context_reasoning="模型给出无法定位的证据。",
            user_visible_reason="内容进入复核。",
            reviewer_reason="证据无法定位。",
        )

    monkeypatch.setattr(moderation_service.provider, "moderate", moderate)
    created = client.post(
        "/api/topics/topic-campus-event/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "一条被模型编造证据的内容。"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending_manual_review"
    assert body["moderation"]["systemDecision"] == "manual_review"


def test_moderation_record_uses_provider_versions(client, monkeypatch):
    from app.api.dependencies import moderation_service

    created = client.post(
        "/api/topics/topic-campus-event/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "一条用于校验版本字段的普通内容。"},
    )
    assert created.status_code == 201
    content_id = created.json()["contentId"]
    detail = client.get(
        f"/api/contents/{content_id}/moderation", headers={"X-User-Id": "reviewer_1"}
    ).json()
    assert detail["provider"] == moderation_service.provider.name
    assert detail["modelVersion"] == moderation_service.provider.model_version


def test_provider_failure_is_routed_to_manual_review(client, monkeypatch):
    from app.api.dependencies import moderation_service

    def fail(_payload):
        raise TimeoutError("mock timeout")

    monkeypatch.setattr(moderation_service.provider, "moderate", fail)
    created = client.post(
        "/api/topics/topic-campus-event/contents",
        headers={"X-User-Id": "student_a"},
        json={"text": "这是一条普通内容，但模拟审核服务超时。"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "pending_manual_review"
    assert body["floorNumber"] is None
    assert body["moderation"]["systemDecision"] == "manual_review"

    detail = client.get(
        f"/api/contents/{body['contentId']}/moderation",
        headers={"X-User-Id": "reviewer_1"},
    ).json()
    assert "TimeoutError" in detail["failureReason"]
