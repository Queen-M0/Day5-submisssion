from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Appeal, AppealAnalysisRecord, AuditLog
from app.providers.ai_provider import AppealInput, ModerationProvider
from app.schemas.common import CounterAnalysisResult
from app.services.context_service import ContextService
from app.services.evidence_service import appeal_sources, validate_evidence


class AppealService:
    def __init__(self, provider: ModerationProvider, context_service: ContextService):
        self.provider = provider
        self.context_service = context_service

    def analyze(self, db: Session, appeal: Appeal) -> CounterAnalysisResult:
        failure_reason = None
        content = appeal.content
        original = content.moderation_records[-1] if content.moderation_records else None
        try:
            context = self.context_service.build(db, content)
            payload = AppealInput(
                appeal_id=appeal.id,
                content=context,
                appeal_type=appeal.appeal_type,
                reason=appeal.reason,
                extra_context=appeal.extra_context,
                original_moderation={
                    "systemDecision": original.system_decision if original else "manual_review",
                    "riskLevel": original.risk_level if original else None,
                    "riskTypes": original.risk_types if original else [],
                    "evidence": original.evidence if original else [],
                    "contextReasoning": original.context_summary if original else "",
                    "uncertainties": original.uncertainties if original else [],
                },
            )
            result = self.provider.analyze_appeal(payload)
            evidence, evidence_valid = validate_evidence(
                result.evidence,
                appeal_sources(payload),
                content.id,
            )
            if result.supports_change and not evidence:
                evidence_valid = False
                failure_reason = "change recommendation has no grounded counter-evidence"
            if not evidence_valid:
                failure_reason = failure_reason or "appeal counter-evidence cannot be grounded"
                result.review_suggestion = "need_more_context"
                if "反证证据无法在输入中定位" not in result.remaining_uncertainties:
                    result.remaining_uncertainties.append("反证证据无法在输入中定位")
        except Exception as exc:
            failure_reason = f"{type(exc).__name__}: {exc}"[:500]
            evidence = []
            evidence_valid = False
            result = CounterAnalysisResult(
                supports_original_decision=[],
                supports_change=[],
                new_evidence_impact="自动反证分析未能完成，不能据此维持或推翻原判。",
                remaining_uncertainties=["申诉反证 Agent 异常，需人工直接核对全部材料。"],
                review_suggestion="need_more_context",
                reviewer_summary="反证分析失败，系统已安全转交人工复核。",
                evidence=[],
            )

        analysis = result.model_dump(by_alias=True)
        analysis["evidenceValidation"] = {"valid": evidence_valid, "items": evidence}
        appeal.counter_analysis = analysis
        appeal.analyzed_at = datetime.now(timezone.utc)
        appeal.status = "reviewing"
        content.status = "appeal_reviewing"
        db.add(
            AppealAnalysisRecord(
                id=str(uuid4()),
                appeal_id=appeal.id,
                provider=self.provider.name,
                prompt_version=self.provider.appeal_prompt_version,
                model_version=self.provider.model_version,
                analysis=analysis,
                evidence_valid=evidence_valid,
                failure_reason=failure_reason,
            )
        )
        db.add(
            AuditLog(
                id=str(uuid4()),
                actor_id="system",
                action="appeal.counter_analysis_failed" if failure_reason else "appeal.counter_analyzed",
                entity_type="content",
                entity_id=content.id,
                detail={
                    "appealId": appeal.id,
                    "provider": self.provider.name,
                    "modelVersion": self.provider.model_version,
                    "promptVersion": self.provider.appeal_prompt_version,
                    "evidenceValid": evidence_valid,
                    "failureReason": failure_reason,
                },
            )
        )
        db.flush()
        return result
