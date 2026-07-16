from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import AuditLog, Content, ModerationRecord
from app.providers.ai_provider import ModerationProvider
from app.schemas.common import ModerationResult
from app.services.context_service import ContextService
from app.services.topic_service import hide_content, publish_content


DECISION_STATUS = {
    "publish": ("published", True),
    "warn": ("published", True),
    "manual_review": ("pending_manual_review", False),
    "limit": ("limited", False),
}

SUGGESTED_ACTION = {"publish": "allow", "warn": "allow", "manual_review": "manual_review", "limit": "limit"}


class ModerationService:
    def __init__(self, provider: ModerationProvider, context_service: ContextService):
        self.provider = provider
        self.context_service = context_service

    def review(self, db: Session, content: Content) -> ModerationResult:
        failure_reason = None
        context_built = False
        try:
            context = self.context_service.build(db, content)
            context_built = True
            result = self.provider.moderate(context)
        except Exception as exc:
            failure_reason = f"{type(exc).__name__}: {exc}"[:500]
            result = ModerationResult(
                is_violation=False,
                risk_level=0,
                risk_score=0,
                risk_types=[],
                confidence=0,
                decision="manual_review",
                context_reasoning="自动审核未能完成，已按安全策略转人工复核。",
                user_visible_reason="自动审核暂时无法完成，内容已进入人工复核。",
                reviewer_reason=f"Provider 调用失败：{failure_reason}",
            )
        evidence = [
            {
                "contentId": content.id,
                "quote": item.text,
                "reason": item.reason,
                "verified": item.text in content.text,
            }
            for item in result.evidence
        ]
        evidence_valid = all(item["verified"] for item in evidence)
        supported_decision = result.decision in DECISION_STATUS
        if not supported_decision:
            failure_reason = f"unsupported decision: {result.decision}"
        system_decision = result.decision if evidence_valid and supported_decision else "manual_review"
        status, is_public = DECISION_STATUS[system_decision]
        if is_public:
            publish_content(db, content)
        else:
            hide_content(content, status)
        context_tags = []
        if result.is_quote_or_report:
            context_tags.append("quote")
        if result.quote_context_safe:
            context_tags.append("counter_speech")
        if result.has_continuous_harassment:
            context_tags.append("repeated_targeting")
        if result.has_implicit_attack:
            context_tags.append("group_pressure")
        target_user_ids = list(result.target_users)
        if not target_user_ids and content.target_user_id:
            target_user_ids.append(content.target_user_id)

        record = ModerationRecord(
            id=str(uuid4()),
            content_id=content.id,
            provider=self.provider.name,
            prompt_version="mock-v1",
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            risk_types=result.risk_types,
            decision=result.decision,
            suggested_action=SUGGESTED_ACTION.get(result.decision, "manual_review"),
            system_decision=system_decision,
            confidence=result.confidence,
            evidence=evidence,
            evidence_valid=evidence_valid,
            context_tags=context_tags,
            intent=result.context_reasoning,
            target_user_ids=target_user_ids,
            context_used=["当前内容", "所属话题"] + (["被回复楼层"] if content.parent_id else []) + ["最近 5 楼"],
            uncertainties=[] if evidence_valid else ["证据原文无法在输入中定位"],
            context_summary=result.context_reasoning,
            user_visible_reason=result.user_visible_reason,
            reviewer_reason=result.reviewer_reason,
            raw_ai_response=result.model_dump(by_alias=True),
            model_version="mock-rules-v1",
            rule_version="community-v1",
            failure_reason=failure_reason,
        )
        db.add(record)
        if context_built:
            db.add(
                AuditLog(
                    id=str(uuid4()),
                    actor_id="system",
                    action="moderation.context_built",
                    entity_type="content",
                    entity_id=content.id,
                    detail={"topicId": content.topic_id, "messageCount": len(context.messages)},
                )
            )
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action="moderation.failed" if failure_reason else "moderation.completed",
                entity_type="content",
                entity_id=content.id,
                detail={
                    "suggestedAction": SUGGESTED_ACTION.get(result.decision, "manual_review"),
                    "systemDecision": system_decision,
                    "failureReason": failure_reason,
                },
            )
        )
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action="evidence.validated",
                entity_type="content",
                entity_id=content.id,
                detail={"valid": evidence_valid, "evidenceCount": len(evidence)},
            )
        )
        action = {
            "publish": "content.published",
            "warn": "content.published",
            "limit": "content.limited",
            "manual_review": "content.manual_review_requested",
        }[system_decision]
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action=action,
                entity_type="content",
                entity_id=content.id,
                detail={"status": content.status, "floorNumber": content.floor_number},
            )
        )
        db.flush()
        return result
