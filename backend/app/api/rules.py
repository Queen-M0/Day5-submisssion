from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AuditLog, ModerationRuleConfig
from app.schemas.requests import UpdateModerationRulesRequest
from app.services.auth_service import demo_user_id, get_current_user, require_reviewer
from app.services.rule_service import get_active_rule_config
from app.services.serializers import iso_utc


router = APIRouter(prefix="/reviewer/rules", tags=["reviewer-rules"])


def rule_dict(rule: ModerationRuleConfig):
    return {
        "id": rule.id,
        "version": rule.version,
        "name": rule.name,
        "enabledRiskTypes": rule.enabled_risk_types or [],
        "autoLimitMinRiskLevel": rule.auto_limit_min_risk_level,
        "manualReviewMinRiskLevel": rule.manual_review_min_risk_level,
        "minConfidence": rule.min_confidence,
        "requireGroundedEvidence": rule.require_grounded_evidence,
        "routeDivergenceToManual": rule.route_divergence_to_manual,
        "isActive": rule.is_active,
        "changeReason": rule.change_reason,
        "updatedBy": rule.updated_by,
        "createdAt": iso_utc(rule.created_at),
    }


def next_version(db: Session) -> str:
    versions = db.scalars(select(ModerationRuleConfig.version)).all()
    numbers = []
    for version in versions:
        if version.startswith("community-v") and version.removeprefix("community-v").isdigit():
            numbers.append(int(version.removeprefix("community-v")))
    return f"community-v{max(numbers, default=0) + 1}"


@router.get("")
def get_rules(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    rule = get_active_rule_config(db)
    db.commit()
    return rule_dict(rule)


@router.get("/history")
def get_rule_history(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    rules = db.scalars(select(ModerationRuleConfig).order_by(ModerationRuleConfig.created_at.desc())).all()
    return {"items": [rule_dict(item) for item in rules]}


@router.put("")
def update_rules(
    payload: UpdateModerationRulesRequest,
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    db.execute(update(ModerationRuleConfig).where(ModerationRuleConfig.is_active.is_(True)).values(is_active=False))
    rule = ModerationRuleConfig(
        id=str(uuid4()),
        version=next_version(db),
        name=payload.name.strip(),
        enabled_risk_types=payload.enabled_risk_types,
        auto_limit_min_risk_level=payload.auto_limit_min_risk_level,
        manual_review_min_risk_level=payload.manual_review_min_risk_level,
        min_confidence=payload.min_confidence,
        require_grounded_evidence=payload.require_grounded_evidence,
        route_divergence_to_manual=payload.route_divergence_to_manual,
        is_active=True,
        change_reason=payload.change_reason.strip(),
        updated_by=user.id,
    )
    db.add(rule)
    db.flush()
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=user.id,
            action="moderation_rules.updated",
            entity_type="rule_config",
            entity_id=rule.id,
            detail={
                "version": rule.version,
                "changeReason": rule.change_reason,
                "autoLimitMinRiskLevel": rule.auto_limit_min_risk_level,
                "manualReviewMinRiskLevel": rule.manual_review_min_risk_level,
                "minConfidence": rule.min_confidence,
            },
        )
    )
    db.commit()
    return rule_dict(rule)
