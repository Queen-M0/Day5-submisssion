from datetime import datetime, timezone
from uuid import uuid4

from app.api.dependencies import appeal_service, moderation_service
from app.core.database import SessionLocal
from app.models import Appeal, AuditLog, Content, ModerationRecord, Scene, Topic, User
from app.services.text_service import normalize_text
from app.services.auth_service import hash_password


USERS = [
    ("student_a", "zhangsan", "张三", "user"),
    ("student_b", "lisi", "李四", "user"),
    ("student_c", "wangwu", "王五", "user"),
    ("reviewer_1", "reviewer", "审核员", "reviewer"),
]

TOPICS = [
    (
        "topic-ai-camp",
        "student_a",
        "团队赛展示怎么分工更高效？",
        "讨论 AI Native 训练营团队赛的产品、开发与答辩分工。",
        "训练营协作",
        128,
        "2026-07-16T01:20:00+00:00",
        "2026-07-16T07:28:00+00:00",
    ),
    (
        "topic-campus-event",
        "student_c",
        "明天路演活动需要提前多久到？",
        "确认集合时间、物料检查和演示设备安排。",
        "校园活动",
        86,
        "2026-07-15T09:15:00+00:00",
        "2026-07-16T03:42:00+00:00",
    ),
    (
        "topic-lost-found",
        "student_b",
        "教学楼三层捡到一张校园卡",
        "校园卡已交到一楼服务台，请失主携带证件领取。",
        "失物招领",
        43,
        "2026-07-14T11:05:00+00:00",
        "2026-07-15T02:10:00+00:00",
    ),
]

PUBLIC_CONTENTS = [
    ("floor-101", "topic-ai-camp", "student_a", "我们先把核心闭环跑通，我负责用户端和内容初审。", None, "2026-07-16T01:20:00+00:00"),
    ("floor-102", "topic-ai-camp", "student_b", "我负责申诉反证和审核员工作台，晚上一起联调。", "floor-101", "2026-07-16T01:28:00+00:00"),
    ("floor-103", "topic-ai-camp", "student_a", "关于迟到我已经解释过原因了，请不要继续说我。", None, "2026-07-16T06:55:00+00:00"),
    ("floor-201", "topic-campus-event", "student_c", "明天九点正式开始，大家觉得几点集合合适？", None, "2026-07-15T09:15:00+00:00"),
    ("floor-202", "topic-campus-event", "student_a", "建议八点二十到，预留设备调试和走台时间。", "floor-201", "2026-07-16T03:42:00+00:00"),
    ("floor-301", "topic-lost-found", "student_b", "卡片姓王，已经交给教学楼一楼服务台。", None, "2026-07-14T11:05:00+00:00"),
    ("floor-302", "topic-lost-found", "student_c", "谢谢，我转发到班级群里问一下。", "floor-301", "2026-07-15T02:10:00+00:00"),
]


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def add_audit(db, actor_id: str, action: str, content_id: str, detail=None) -> None:
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            entity_type="content",
            entity_id=content_id,
            detail=detail or {},
        )
    )


def add_quote_misread_record(db, content: Content) -> None:
    quote = "你这种人不配待在这里"
    db.add(
        ModerationRecord(
            id=str(uuid4()),
            content_id=content.id,
            provider="mock-ai",
            prompt_version="seed-v1",
            risk_level=3,
            risk_score=88,
            risk_types=["insult"],
            decision="limit",
            suggested_action="limit",
            system_decision="limit",
            confidence=0.78,
            evidence=[{"contentId": content.id, "quote": quote, "reason": "包含明显排斥与人身攻击表达。", "verified": True}],
            evidence_valid=True,
            context_tags=["context_missing"],
            intent="初审认为内容包含针对他人的直接攻击",
            target_user_ids=["student_b"],
            context_used=["当前内容", "所属话题", "最近 2 楼"],
            uncertainties=["引用来源未被初审正确关联"],
            context_summary="引用来源未被第一次审核正确关联。",
            user_visible_reason="内容包含可能针对他人的攻击性表达，当前暂不公开。",
            reviewer_reason="用户主张存在引用关系，请结合补充上下文复核说话者与真实意图。",
            raw_ai_response={"seedCase": "quote_misread"},
            model_version="mock-rules-v1",
            rule_version="community-v1",
        )
    )
    add_audit(db, "system", "moderation.completed", content.id, {"systemDecision": "limit"})
    add_audit(db, "system", "evidence.validated", content.id, {"valid": True, "evidenceCount": 1})
    add_audit(db, "system", "content.limited", content.id, {"status": "limited"})


def seed() -> None:
    db = SessionLocal()
    try:
        for user_id, username, display_name, role in USERS:
            user = db.get(User, user_id)
            if not user:
                password = "review123" if role in {"reviewer", "admin"} else "user123"
                user = User(id=user_id, username=username, display_name=display_name, role=role, password_hash=hash_password(password))
                db.add(user)
            else:
                user.username = username
                user.display_name = display_name
                user.role = role
                if not user.password_hash:
                    password = "review123" if role in {"reviewer", "admin"} else "user123"
                    user.password_hash = hash_password(password)

        scene = db.get(Scene, "community-001")
        if not scene:
            scene = Scene(id="community-001")
            db.add(scene)
        scene.type = "community"
        scene.title = "AI Native 青年讨论社区"
        scene.description = "一个带上下文审核和申诉复核能力的文字社区"
        db.flush()

        for topic_id, author_id, title, summary, category, view_count, created_at, last_active_at in TOPICS:
            topic = db.get(Topic, topic_id)
            if not topic:
                topic = Topic(id=topic_id, scene_id=scene.id, author_id=author_id)
                db.add(topic)
            topic.title = title
            topic.summary = summary
            topic.category = category
            topic.status = "published"
            topic.visible_to_public = True
            topic.view_count = view_count
            topic.created_at = dt(created_at)
            topic.last_active_at = dt(last_active_at)
        db.flush()

        for content_id, topic_id, author_id, text, parent_id, created_at in PUBLIC_CONTENTS:
            if db.get(Content, content_id):
                continue
            parent = db.get(Content, parent_id) if parent_id else None
            content = Content(
                id=content_id,
                scene_id=scene.id,
                topic_id=topic_id,
                content_type="topic_root" if parent_id is None and content_id.endswith("01") else "forum_reply",
                author_id=author_id,
                parent_id=parent_id,
                target_user_id=parent.author_id if parent else None,
                text=text,
                normalized_text=normalize_text(text),
                status="pending_ai_review",
                visible_to_public=False,
                created_at=dt(created_at),
            )
            db.add(content)
            db.flush()
            add_audit(db, author_id, "content.submitted", content.id, {"topicId": topic_id})
            moderation_service.review(db, content)

        if not db.get(Content, "floor-quote"):
            quote_content = Content(
                id="floor-quote",
                scene_id=scene.id,
                topic_id="topic-ai-camp",
                content_type="forum_reply",
                author_id="student_a",
                text="他说“你这种人不配待在这里”，这种攻击别人的表达很不合适。",
                normalized_text=normalize_text("他说“你这种人不配待在这里”，这种攻击别人的表达很不合适。"),
                status="appeal_submitted",
                visible_to_public=False,
                created_at=dt("2026-07-16T07:12:00+00:00"),
            )
            db.add(quote_content)
            db.flush()
            add_audit(db, "student_a", "content.submitted", quote_content.id, {"topicId": "topic-ai-camp"})
            add_quote_misread_record(db, quote_content)

        if not db.get(Content, "floor-harassment"):
            parent = db.get(Content, "floor-103")
            content = Content(
                id="floor-harassment",
                scene_id=scene.id,
                topic_id="topic-ai-camp",
                content_type="forum_reply",
                author_id="student_b",
                parent_id=parent.id,
                target_user_id=parent.author_id,
                text="大家都看看他平时是什么样。",
                normalized_text=normalize_text("大家都看看他平时是什么样。"),
                status="pending_ai_review",
                visible_to_public=False,
                created_at=dt("2026-07-16T07:28:00+00:00"),
            )
            db.add(content)
            db.flush()
            add_audit(db, "student_b", "content.submitted", content.id, {"topicId": "topic-ai-camp"})
            moderation_service.review(db, content)

        appeal = db.get(Appeal, "appeal-quote")
        if not appeal:
            appeal = Appeal(
                id="appeal-quote",
                content_id="floor-quote",
                user_id="student_a",
                appeal_type="quote_or_report",
                reason="前半句是引用 2 楼的原话，我是在批评这种表达，并不是攻击李四。",
                extra_context="被引用内容来自讨论现场的原话；后半句明确说明这种表达很不合适。",
                counter_analysis={},
                analyzed_at=None,
                status="submitted",
                created_at=dt("2026-07-16T07:18:00+00:00"),
            )
            db.add(appeal)
            add_audit(db, "student_a", "appeal.submitted", "floor-quote", {"appealId": appeal.id})
            db.flush()
        if not appeal.counter_analysis:
            appeal_service.analyze(db, appeal)

        for topic_id, _, _, _, _, view_count, _, last_active_at in TOPICS:
            topic = db.get(Topic, topic_id)
            topic.view_count = view_count
            topic.last_active_at = dt(last_active_at)
        db.commit()
        print("Demo seed is ready.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
