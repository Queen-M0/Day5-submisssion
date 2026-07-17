from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Appeal, AppealAnalysisRecord, AuditLog, Content
from app.providers.ai_provider import AppealContext, AppealCriticInput, AppealInput
from app.services.context_service import ContextService
from app.services.evidence_service import appeal_sources, validate_evidence


class AppealService:
    """Runs the appeal re-review agent and persists each analysis run."""

    def __init__(self, critic, context_service: ContextService):
        self.critic = critic
        self.context_service = context_service

    def analyze(self, db: Session, appeal: Appeal, content: Optional[Content] = None) -> Optional[Dict[str, Any]]:
        content = content or appeal.content
        original = content.moderation_records[-1] if content.moderation_records else None
        if original is None:
            return self._record_failure(db, appeal, content, "ValueError: content has no initial moderation record")

        try:
            context = self.context_service.build(db, content)
            if hasattr(self.critic, "critique"):
                analysis, evidence_valid = self._run_split_critic(appeal, content, original, context)
            elif hasattr(self.critic, "analyze_appeal"):
                analysis, evidence_valid = self._run_unified_provider(appeal, content, original, context)
            else:
                raise TypeError("appeal critic does not implement critique or analyze_appeal")
        except Exception as exc:  # noqa: BLE001 - preserve appeal rights on any AI failure
            return self._record_failure(db, appeal, content, f"{type(exc).__name__}: {exc}"[:500])

        appeal.counter_analysis = analysis
        appeal.analyzed_at = datetime.now(timezone.utc)
        appeal.status = "reviewing"
        content.status = "appeal_reviewing"
        db.add(
            AppealAnalysisRecord(
                id=str(uuid4()),
                appeal_id=appeal.id,
                provider=getattr(self.critic, "name", "unknown"),
                prompt_version=getattr(
                    self.critic,
                    "appeal_prompt_version",
                    getattr(self.critic, "prompt_version", "unknown"),
                ),
                model_version=getattr(self.critic, "model_version", "unknown"),
                analysis=analysis,
                evidence_valid=evidence_valid,
                failure_reason=None,
            )
        )
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action="appeal.counter_analyzed",
                entity_type="content",
                entity_id=content.id,
                detail={
                    "appealId": appeal.id,
                    "provider": getattr(self.critic, "name", "unknown"),
                    "modelVersion": getattr(self.critic, "model_version", "unknown"),
                    "evidenceValid": evidence_valid,
                },
            )
        )
        db.flush()
        return analysis

    def _run_split_critic(self, appeal: Appeal, content: Content, original, context) -> tuple[Dict[str, Any], bool]:
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
                review_id=original.id,
                decision=original.decision,
                system_decision=original.system_decision,
                risk_level=original.risk_level,
                risk_score=original.risk_score,
                risk_types=list(original.risk_types or []),
                confidence=original.confidence,
                user_visible_reason=original.user_visible_reason,
                reviewer_reason=original.reviewer_reason,
                evidence=list(original.evidence or []),
            ),
            parent_text=context.parent_text,
            parent_id=context.parent_id,
            parent_author_id=context.parent_author_id,
            context_messages=[*context.messages, *context.author_history, *context.target_history],
        )
        result = self.critic.critique(payload)
        sources = {
            content.id: content.text,
            "appeal-reason": appeal.reason,
            "appeal-extra-context": appeal.extra_context,
        }
        if context.parent_id and context.parent_text:
            sources[context.parent_id] = context.parent_text
        for message in [*context.messages, *context.author_history, *context.target_history]:
            sources[message.id] = message.text
        evidence, evidence_valid = validate_evidence(result.evidence, sources, content.id)
        analysis = result.model_dump(by_alias=True, exclude_none=True)
        reviewer_summary = analysis.get("reviewSuggestion") or analysis.get("reasoning", "")
        suggestion_map = {
            "uphold": "maintain_limit",
            "overturn_allow": "allow",
            "overturn_limit": "maintain_limit",
            "need_manual": "need_more_context",
        }
        analysis["reviewSuggestion"] = suggestion_map.get(
            analysis.get("recommendedDecision", ""),
            analysis.get("reviewSuggestion", "need_more_context"),
        )
        analysis.update(
            {
                "provider": getattr(self.critic, "name", "unknown"),
                "modelVersion": getattr(self.critic, "model_version", "unknown"),
                "promptVersion": getattr(
                    self.critic,
                    "appeal_prompt_version",
                    getattr(self.critic, "prompt_version", "unknown"),
                ),
                "ruleVersion": getattr(self.critic, "rule_version", "unknown"),
                "initialReviewId": original.id,
                "evidenceValid": evidence_valid,
                "evidence": evidence,
                "evidenceValidation": {"valid": evidence_valid, "items": evidence},
                "reviewerSummary": analysis.get("reviewerSummary") or reviewer_summary,
            }
        )
        return analysis, evidence_valid

    def _run_unified_provider(self, appeal: Appeal, content: Content, original, context) -> tuple[Dict[str, Any], bool]:
        payload = AppealInput(
            appeal_id=appeal.id,
            content=context,
            appeal_type=appeal.appeal_type,
            reason=appeal.reason,
            extra_context=appeal.extra_context,
            original_moderation={
                "systemDecision": original.system_decision,
                "riskLevel": original.risk_level,
                "riskTypes": original.risk_types or [],
                "evidence": original.evidence or [],
                "contextReasoning": original.context_summary,
                "uncertainties": original.uncertainties or [],
            },
        )
        result = self.critic.analyze_appeal(payload)
        evidence, evidence_valid = validate_evidence(result.evidence, appeal_sources(payload), content.id)
        if result.supports_change and not evidence:
            evidence_valid = False
        analysis = result.model_dump(by_alias=True)
        analysis["evidence"] = evidence
        analysis["evidenceValidation"] = {"valid": evidence_valid, "items": evidence}
        return analysis, evidence_valid

    def _record_failure(self, db: Session, appeal: Appeal, content: Content, failure_reason: str) -> None:
        db.add(
            AppealAnalysisRecord(
                id=str(uuid4()),
                appeal_id=appeal.id,
                provider=getattr(self.critic, "name", "unknown"),
                prompt_version=getattr(
                    self.critic,
                    "appeal_prompt_version",
                    getattr(self.critic, "prompt_version", "unknown"),
                ),
                model_version=getattr(self.critic, "model_version", "unknown"),
                analysis={},
                evidence_valid=False,
                failure_reason=failure_reason,
            )
        )
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action="appeal.counter_analysis_failed",
                entity_type="content",
                entity_id=content.id,
                detail={"appealId": appeal.id, "failureReason": failure_reason},
            )
        )
        db.flush()
        return None
