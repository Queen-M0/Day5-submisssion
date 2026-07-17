from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import AuditLog, Content, ModerationComparison, ModerationRecord
from app.providers.ai_provider import ModerationProvider
from app.schemas.common import ModerationResult
from app.services.context_service import ContextService
from app.services.evidence_service import moderation_sources, validate_evidence
from app.services.rule_service import apply_moderation_policy, get_active_rule_config
from app.services.topic_service import hide_content, publish_content


DECISION_STATUS = {
    "publish": ("published", True),
    "warn": ("published", True),
    "manual_review": ("pending_manual_review", False),
    "limit": ("limited", False),
}

SUGGESTED_ACTION = {"publish": "allow", "warn": "allow", "manual_review": "manual_review", "limit": "limit"}


class ModerationService:
    def __init__(
        self,
        provider: ModerationProvider,
        context_service: ContextService,
        secondary_provider: ModerationProvider | None = None,
    ):
        self.provider = provider
        self.context_service = context_service
        self.secondary_provider = secondary_provider

    def review(self, db: Session, content: Content) -> ModerationResult:
        rule_config = get_active_rule_config(db)
        failure_reason = None
        context_built = False
        context = None
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
        sources = moderation_sources(context) if context is not None else {content.id: content.text}
        evidence, evidence_valid = validate_evidence(result.evidence, sources, content.id)
        if result.decision == "limit" and not evidence:
            evidence_valid = False
            failure_reason = "high-risk decision has no grounded evidence"
        elif not evidence_valid:
            failure_reason = "AI evidence cannot be grounded in the supplied context"
        supported_decision = result.decision in DECISION_STATUS
        if not supported_decision:
            failure_reason = f"unsupported decision: {result.decision}"
        system_decision = result.decision if evidence_valid and supported_decision else "manual_review"

        secondary_result = None
        secondary_evidence = []
        secondary_evidence_valid = True
        secondary_failure_reason = None
        divergence_reasons = []
        if self.secondary_provider is not None and context is not None and failure_reason is None:
            try:
                secondary_result = self.secondary_provider.moderate(context)
                secondary_evidence, secondary_evidence_valid = validate_evidence(
                    secondary_result.evidence,
                    sources,
                    content.id,
                )
                if secondary_result.decision == "limit" and not secondary_evidence:
                    secondary_evidence_valid = False
                if not secondary_evidence_valid:
                    divergence_reasons.append("辅助模型证据无法在输入中定位")
                if secondary_result.decision != result.decision:
                    divergence_reasons.append(
                        f"建议动作不一致：主模型 {result.decision}，辅助模型 {secondary_result.decision}"
                    )
                if abs(secondary_result.risk_level - result.risk_level) >= 2:
                    divergence_reasons.append(
                        f"风险等级差异过大：主模型 L{result.risk_level}，辅助模型 L{secondary_result.risk_level}"
                    )
                primary_risks = set(result.risk_types)
                secondary_risks = set(secondary_result.risk_types)
                if (
                    result.risk_level >= 2
                    and secondary_result.risk_level >= 2
                    and primary_risks
                    and secondary_risks
                    and primary_risks.isdisjoint(secondary_risks)
                ):
                    divergence_reasons.append("两路模型识别的高风险类型没有交集")
            except Exception as exc:
                secondary_failure_reason = f"{type(exc).__name__}: {exc}"[:500]
                secondary_evidence_valid = False
                divergence_reasons.append("辅助模型调用失败，无法完成双模型一致性检查")

            if divergence_reasons and secondary_failure_reason:
                failure_reason = f"secondary provider failed: {secondary_failure_reason}"[:500]

        policy_reasons: list[str] = []
        if supported_decision:
            system_decision, policy_reasons = apply_moderation_policy(
                result=result,
                evidence_valid=evidence_valid,
                has_dual_divergence=bool(divergence_reasons),
                config=rule_config,
            )
        if not supported_decision:
            system_decision = "manual_review"

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

        dual_uncertainties = [f"双模型分歧：{item}" for item in divergence_reasons]
        policy_uncertainties = [f"规则分流：{item}" for item in policy_reasons]
        user_visible_reason = result.user_visible_reason
        reviewer_reason = result.reviewer_reason
        if divergence_reasons:
            user_visible_reason = (
                "双模型复核未能完整完成，内容已安全转入人工复核。"
                if secondary_failure_reason
                else "两路 AI 审核结果存在分歧，内容已转入人工复核。"
            )
            reviewer_reason = f"{reviewer_reason}\n双模型检查：{'；'.join(divergence_reasons)}"
        if policy_reasons:
            reviewer_reason = f"{reviewer_reason}\n规则 {rule_config.version}：{'；'.join(policy_reasons)}"
            if system_decision == "manual_review" and not divergence_reasons:
                user_visible_reason = "当前结果触发审核安全阈值，内容已转入人工复核。"

        record = ModerationRecord(
            id=str(uuid4()),
            content_id=content.id,
            provider=self.provider.name,
            prompt_version=self.provider.moderation_prompt_version,
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
            intent=result.intent or result.context_reasoning,
            target_user_ids=target_user_ids,
            context_used=result.context_used or (["当前内容", "所属话题"] + (["被回复楼层"] if content.parent_id else []) + ["最近 5 楼", "作者历史", "目标用户历史"]),
            uncertainties=(result.uncertainties or []) + ([] if evidence_valid else ["证据原文无法在输入中定位"]) + dual_uncertainties + policy_uncertainties,
            context_summary=result.context_reasoning,
            user_visible_reason=user_visible_reason,
            reviewer_reason=reviewer_reason,
            raw_ai_response=result.model_dump(by_alias=True),
            model_version=self.provider.model_version,
            rule_version=rule_config.version,
            failure_reason=failure_reason,
        )
        db.add(record)
        db.flush()
        if self.secondary_provider is not None and context is not None and (secondary_result is not None or secondary_failure_reason):
            comparison = ModerationComparison(
                id=str(uuid4()),
                content_id=content.id,
                primary_record_id=record.id,
                secondary_provider=self.secondary_provider.name,
                secondary_model_version=self.secondary_provider.model_version,
                secondary_prompt_version=self.secondary_provider.moderation_prompt_version,
                secondary_decision=secondary_result.decision if secondary_result else "error",
                secondary_risk_level=secondary_result.risk_level if secondary_result else 0,
                secondary_risk_types=secondary_result.risk_types if secondary_result else [],
                secondary_evidence=secondary_evidence,
                secondary_evidence_valid=secondary_evidence_valid,
                secondary_raw_response=secondary_result.model_dump(by_alias=True) if secondary_result else {},
                divergent=bool(divergence_reasons),
                divergence_reasons=divergence_reasons,
                system_resolution=system_decision if divergence_reasons else "agree",
                failure_reason=secondary_failure_reason,
            )
            db.add(comparison)
            db.add(
                AuditLog(
                    id=str(uuid4()),
                    actor_id="system",
                    action=(
                        "moderation.dual_review_failed"
                        if secondary_failure_reason
                        else "moderation.divergence_detected"
                        if divergence_reasons
                        else "moderation.dual_review_completed"
                    ),
                    entity_type="content",
                    entity_id=content.id,
                    detail={
                        "primaryModel": self.provider.model_version,
                        "secondaryModel": self.secondary_provider.model_version,
                        "divergent": bool(divergence_reasons),
                        "reasons": divergence_reasons,
                        "ruleVersion": rule_config.version,
                        "systemResolution": system_decision,
                    },
                )
            )
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
                    "ruleVersion": rule_config.version,
                    "policyReasons": policy_reasons,
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
