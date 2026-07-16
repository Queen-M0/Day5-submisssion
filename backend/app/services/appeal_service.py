from typing import Any, Dict, List, Optional

from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Appeal, AuditLog, Content
from app.providers.ai_provider import AppealContext, AppealCriticInput, AppealCriticProvider
from app.services.context_service import ContextService
from app.services.serializers import iso_utc


class AppealService:
    """Runs the appeal re-review ("counter-argument") agent.

    Responsibilities (matching the three-layer design:
    AI argues, code validates, human decides):
    - Consume the *persisted* initial moderation record (time-decoupled) so the
      re-review cannot silently drift from the first verdict.
    - Validate any cited evidence against real floor text (same cross-context
      pitfall guard used by the initial moderation).
    - On provider failure, route to manual review instead of crashing.
    """

    def __init__(self, critic: AppealCriticProvider, context_service: ContextService):
        self.critic = critic
        self.context_service = context_service

    def analyze(self, db: Session, appeal: Appeal, content: Content) -> Optional[Dict[str, Any]]:
        """Generate the counter_analysis for an appeal.

        Returns the counter_analysis dict on success, or None when the critic
        could not run (caller should keep the appeal in the manual queue).
        """
        failure_reason: Optional[str] = None
        counter: Optional[Dict[str, Any]] = None
        try:
            record = content.moderation_records[-1] if content.moderation_records else None
            if record is None:
                raise ValueError("content has no initial moderation record to critique")

            context = self.context_service.build(db, content)
            payload = AppealCriticInput(
                content_id=content.id,
                author_id=content.author_id,
                author_name=content.author.display_name,
                text=content.text,
                topic_title=content.topic.title,
                appeal_type=appeal.appeal_type,
                appeal_reason=appeal.reason,
                extra_context=appeal.extra_context,
                initial_review=AppealContext(
                    review_id=record.id,
                    decision=record.decision,
                    system_decision=record.system_decision,
                    risk_level=record.risk_level,
                    risk_score=record.risk_score,
                    risk_types=list(record.risk_types or []),
                    confidence=record.confidence,
                    user_visible_reason=record.user_visible_reason,
                    reviewer_reason=record.reviewer_reason,
                    evidence=list(record.evidence or []),
                ),
                parent_text=context.parent_text,
                parent_id=context.parent_id,
                parent_author_id=context.parent_author_id,
                context_messages=context.messages,
            )
            result = self.critic.critique(payload)

            # Cross-context evidence validation: every cited quote must exist
            # verbatim in the original content, a context floor, or the replied
            # floor. Fabricated quotes are flagged and excluded from trust.
            source_texts: Dict[str, str] = {content.id: content.text}
            for message in context.messages:
                source_texts[message.id] = message.text
            if context.parent_text is not None and context.parent_id:
                source_texts[context.parent_id] = context.parent_text

            evidence: List[Dict[str, Any]] = []
            for item in result.evidence:
                cited_id = item.content_id or content.id
                cited_text = source_texts.get(cited_id)
                verified = cited_text is not None and item.text in cited_text
                evidence.append(
                    {
                        "contentId": cited_id,
                        "quote": item.text,
                        "reason": item.reason,
                        "verified": verified,
                    }
                )
            evidence_valid = all(item["verified"] for item in evidence) if evidence else True

            core = result.model_dump(by_alias=True, exclude_none=True)
            counter = {
                "provider": self.critic.name,
                "modelVersion": self.critic.model_version,
                "promptVersion": self.critic.prompt_version,
                "ruleVersion": self.critic.rule_version,
                "initialReviewId": record.id,
                "evidenceValid": evidence_valid,
                **core,
            }
            counter["evidence"] = evidence

            db.add(
                AuditLog(
                    id=str(uuid4()),
                    actor_id="system",
                    action="appeal.ai_critic_completed",
                    entity_type="content",
                    entity_id=content.id,
                    detail={
                        "appealId": appeal.id,
                        "upholdsInitial": result.upholds_initial,
                        "recommendedDecision": result.recommended_decision,
                        "evidenceValid": evidence_valid,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001 - route any critic failure to manual
            failure_reason = f"{type(exc).__name__}: {exc}"[:500]
            db.add(
                AuditLog(
                    id=str(uuid4()),
                    actor_id="system",
                    action="appeal.ai_critic_failed",
                    entity_type="content",
                    entity_id=content.id,
                    detail={"appealId": appeal.id, "failureReason": failure_reason},
                )
            )

        return counter
