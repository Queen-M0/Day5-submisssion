from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Content, ModerationRecord
from app.providers.ai_provider import ModerationProvider
from app.schemas.common import ModerationResult
from app.services.context_service import ContextService


DECISION_STATUS = {
    "publish": ("published", True),
    "warn": ("published", True),
    "manual_review": ("pending_manual_review", False),
    "limit": ("limited", False),
}


class ModerationService:
    def __init__(self, provider: ModerationProvider, context_service: ContextService):
        self.provider = provider
        self.context_service = context_service

    def review(self, db: Session, content: Content) -> ModerationResult:
        context = self.context_service.build(db, content)
        result = self.provider.moderate(context)
        status, is_public = DECISION_STATUS[result.decision]
        content.status = status
        content.visible_to_public = is_public

        record = ModerationRecord(
            id=str(uuid4()),
            content_id=content.id,
            provider=self.provider.name,
            prompt_version="mock-v1",
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            risk_types=result.risk_types,
            decision=result.decision,
            confidence=result.confidence,
            evidence=[item.model_dump(by_alias=True) for item in result.evidence],
            context_summary=result.context_reasoning,
            user_visible_reason=result.user_visible_reason,
            reviewer_reason=result.reviewer_reason,
            raw_ai_response=result.model_dump(by_alias=True),
        )
        db.add(record)
        db.commit()
        db.refresh(content)
        return result

