from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models import Content, ModerationRecord, Topic, User


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
        "decision": record.system_decision,
        "suggestedAction": record.suggested_action,
        "systemDecision": record.system_decision,
        "confidence": record.confidence,
        "contextTags": record.context_tags or [],
        "intent": record.intent,
        "targetUserIds": record.target_user_ids or [],
        "contextUsed": record.context_used or [],
        "uncertainties": record.uncertainties or [],
        "evidence": record.evidence or [],
        "evidenceValid": record.evidence_valid,
        "userVisibleReason": record.user_visible_reason,
        "dualReview": None
        if not record.comparison
        else {
            "enabled": True,
            "primary": {
                "provider": record.provider,
                "modelVersion": record.model_version,
                "decision": record.decision,
                "riskLevel": record.risk_level,
                "riskTypes": record.risk_types or [],
            },
            "secondary": {
                "provider": record.comparison.secondary_provider,
                "modelVersion": record.comparison.secondary_model_version,
                "promptVersion": record.comparison.secondary_prompt_version,
                "decision": record.comparison.secondary_decision,
                "riskLevel": record.comparison.secondary_risk_level,
                "riskTypes": record.comparison.secondary_risk_types or [],
                "evidenceValid": record.comparison.secondary_evidence_valid,
            },
            "divergent": record.comparison.divergent,
            "reasons": record.comparison.divergence_reasons or [],
            "systemResolution": record.comparison.system_resolution,
            "failureReason": record.comparison.failure_reason,
        },
    }
    if detailed:
        value.update(
            {
                "contextReasoning": record.context_summary,
                "reviewerReason": record.reviewer_reason,
                "rawResult": record.raw_ai_response,
                "provider": record.provider,
                "modelVersion": record.model_version,
                "promptVersion": record.prompt_version,
                "ruleVersion": record.rule_version,
                "failureReason": record.failure_reason,
            }
        )
    return value


def content_dict(content: Content, current_user_id: Optional[str] = None, detailed: bool = False) -> Dict[str, Any]:
    record = content.moderation_records[-1] if content.moderation_records else None
    can_view_text = content.visible_to_public or content.author_id == current_user_id or detailed
    return {
        "id": content.id,
        "sceneId": content.scene_id,
        "topicId": content.topic_id,
        "floorNumber": content.floor_number,
        "contentType": content.content_type,
        "author": user_dict(content.author),
        "parentId": content.parent_id,
        "parentAuthorName": content.parent.author.display_name if content.parent else None,
        "replyTo": None
        if not content.parent
        else {
            "contentId": content.parent.id,
            "floorNumber": content.parent.floor_number,
            "authorName": content.parent.author.display_name,
            "textPreview": content.parent.text[:80],
        },
        "text": content.text if can_view_text else "该内容暂未公开",
        "status": content.status,
        "visibleToPublic": content.visible_to_public,
        "createdAt": iso_utc(content.created_at),
        "moderation": moderation_summary(record, detailed=detailed) if can_view_text else None,
    }


def topic_dict(topic: Topic) -> Dict[str, Any]:
    public_contents = [item for item in topic.contents if item.visible_to_public]
    public_contents.sort(key=lambda item: item.floor_number or 0)
    last_content = public_contents[-1] if public_contents else None
    return {
        "id": topic.id,
        "sceneId": topic.scene_id,
        "title": topic.title,
        "summary": topic.summary,
        "category": topic.category,
        "author": user_dict(topic.author),
        "status": topic.status,
        "visibleToPublic": topic.visible_to_public,
        "publicFloorCount": len(public_contents),
        "viewCount": topic.view_count,
        "lastReplyAuthorName": last_content.author.display_name if last_content else None,
        "createdAt": iso_utc(topic.created_at),
        "lastActiveAt": iso_utc(topic.last_active_at),
    }
