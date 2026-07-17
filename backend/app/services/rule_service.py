from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ModerationRuleConfig
from app.schemas.common import ModerationResult


DEFAULT_RISK_TYPES = ["insult", "harassment", "threat", "fraud", "discrimination", "implicit_attack"]


def get_active_rule_config(db: Session) -> ModerationRuleConfig:
    config = db.scalar(
        select(ModerationRuleConfig)
        .where(ModerationRuleConfig.is_active.is_(True))
        .order_by(ModerationRuleConfig.created_at.desc())
    )
    if config:
        return config
    config = ModerationRuleConfig(
        id=str(uuid4()),
        version="community-v1",
        name="社区审核默认规则",
        enabled_risk_types=DEFAULT_RISK_TYPES,
        auto_limit_min_risk_level=3,
        manual_review_min_risk_level=2,
        min_confidence=0.65,
        require_grounded_evidence=True,
        route_divergence_to_manual=True,
        is_active=True,
        change_reason="初始化默认规则",
        updated_by="system",
    )
    db.add(config)
    db.flush()
    return config


def apply_moderation_policy(
    result: ModerationResult,
    evidence_valid: bool,
    has_dual_divergence: bool,
    config: ModerationRuleConfig,
) -> tuple[str, list[str]]:
    decision = result.decision
    reasons: list[str] = []
    if config.require_grounded_evidence and not evidence_valid:
        return "manual_review", ["证据真实性校验未通过"]
    unsupported_risks = [item for item in result.risk_types if item not in config.enabled_risk_types and item != "safe_context"]
    if unsupported_risks and result.risk_level > 0:
        reasons.append(f"风险类型未启用自动处置：{', '.join(unsupported_risks)}")
    if result.confidence < config.min_confidence:
        reasons.append(f"模型置信度 {result.confidence:.2f} 低于阈值 {config.min_confidence:.2f}")
    if has_dual_divergence and config.route_divergence_to_manual:
        reasons.append("规则要求双模型分歧转人工")
    # 安全兜底条件优先级最高，不能再被后面的自动限制规则覆盖。
    if reasons:
        return "manual_review", reasons
    if (
        result.is_violation
        and result.risk_level >= config.auto_limit_min_risk_level
        and evidence_valid
        and not result.quote_context_safe
    ):
        decision = "limit"
        reasons.append(f"风险等级达到自动限制阈值 L{config.auto_limit_min_risk_level}")
    elif result.risk_level >= config.manual_review_min_risk_level and decision == "publish":
        decision = "manual_review"
        reasons.append(f"风险等级达到人工复核阈值 L{config.manual_review_min_risk_level}")
    return decision, reasons
