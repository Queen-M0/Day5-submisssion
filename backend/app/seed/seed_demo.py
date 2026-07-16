from datetime import datetime, timedelta, timezone
from app.api.dependencies import moderation_service
from app.core.database import SessionLocal
from app.models import Content, Scene, User
from app.services.text_service import normalize_text


USERS = [
    User(id="student_a", username="student_a", display_name="林晓", role="user"),
    User(id="student_b", username="student_b", display_name="周然", role="user"),
    User(id="reviewer_1", username="reviewer_1", display_name="陈审核员", role="reviewer"),
    User(id="admin_1", username="admin_1", display_name="系统管理员", role="admin"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for user in USERS:
            if not db.get(User, user.id):
                db.add(user)
        if not db.get(Scene, "campus_forum_001"):
            db.add(
                Scene(
                    id="campus_forum_001",
                    type="forum_thread",
                    title="校园交流社区",
                    description="围绕小组作业与校园生活展开讨论，每一楼在公开前都会经过上下文审核。",
                )
            )
        db.commit()

        base_time = datetime.now(timezone.utc) - timedelta(minutes=18)
        rows = [
            ("seed_001", "student_b", "这次小组作业我们今晚八点开会讨论吧。", None),
            ("seed_002", "student_a", "我来负责这次展示，也可以先把提纲发群里。", "seed_001"),
            ("seed_003", "student_b", "楼上说“你就是废物”这种话不合适，请管理员处理。", "seed_002"),
            ("seed_004", "student_a", "你就是废物，别来拖累我们。", "seed_001"),
            ("seed_005", "student_b", "别让那个“大聪明”碰展示，懂的都懂。", "seed_002"),
        ]
        for index, (content_id, author_id, text, parent_id) in enumerate(rows):
            if not db.get(Content, content_id):
                content = Content(
                    id=content_id,
                    scene_id="campus_forum_001",
                    content_type="forum_reply",
                    author_id=author_id,
                    parent_id=parent_id,
                    text=text,
                    normalized_text=normalize_text(text),
                    status="pending_ai_review",
                    visible_to_public=False,
                    created_at=base_time + timedelta(minutes=index * 3),
                )
                db.add(content)
                db.flush()
                db.refresh(content, attribute_names=["author", "parent"])
                moderation_service.review(db, content)
        print("Demo seed is ready.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
