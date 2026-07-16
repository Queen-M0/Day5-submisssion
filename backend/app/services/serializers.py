from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models import Content, ModerationRecord, User


def iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def user_dict(user: User) -> Dict[str, str]:
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "role": user.role,
    }


def moderation_summary(record: Optional[ModerationRecord], detailed: bool = False) -> Optional[Dict[str, Any]]:
    if not record:
        return None
    value: Dict[str, Any] = {
        "riskLevel": record.risk_level,
        "riskScore": record.risk_score,
        "riskTypes": record.risk_types,
        "decision": record.decision,
        "confidence": record.confidence,
        "userVisibleReason": record.user_visible_reason,
    }
    if detailed:
        value.update(
            {
                "evidence": record.evidence,
                "contextReasoning": record.context_summary,
                "reviewerReason": record.reviewer_reason,
                "rawResult": record.raw_ai_response,
            }
        )
    return value


def content_dict(content: Content, current_user_id: Optional[str] = None, detailed: bool = False) -> Dict[str, Any]:
    record = content.moderation_records[-1] if content.moderation_records else None
    can_view_text = content.visible_to_public or content.author_id == current_user_id or detailed
    return {
        "id": content.id,
        "sceneId": content.scene_id,
        "contentType": content.content_type,
        "author": user_dict(content.author),
        "parentId": content.parent_id,
        "parentAuthorName": content.parent.author.display_name if content.parent else None,
        "text": content.text if can_view_text else "该内容暂未公开",
        "status": content.status,
        "visibleToPublic": content.visible_to_public,
        "createdAt": iso_utc(content.created_at),
        "moderation": moderation_summary(record, detailed=detailed) if can_view_text else None,
    }
