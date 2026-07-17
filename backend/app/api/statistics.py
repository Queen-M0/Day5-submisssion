from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import moderation_service
from app.core.database import get_db
from app.models import Appeal, Content, ManualReview, ModerationComparison, ModerationRecord
from app.services.auth_service import demo_user_id, get_current_user, require_reviewer
from app.services.rule_service import get_active_rule_config


router = APIRouter(prefix="/reviewer/statistics", tags=["reviewer-statistics"])


def percentage(numerator: int, denominator: int) -> float:
    return round(numerator * 100 / denominator, 1) if denominator else 0.0


@router.get("")
def get_statistics(
    user_id: str = Depends(demo_user_id),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, user_id)
    require_reviewer(user)
    contents = db.scalars(select(Content)).all()
    appeals = db.scalars(select(Appeal)).all()
    reviews = db.scalars(select(ManualReview)).all()
    comparisons = db.scalars(select(ModerationComparison)).all()
    records = db.scalars(select(ModerationRecord).order_by(ModerationRecord.created_at)).all()
    latest_by_content = {record.content_id: record for record in records}
    latest_records = list(latest_by_content.values())

    decided_appeals = [appeal for appeal in appeals if appeal.status in {"approved", "rejected"}]
    approved_appeals = sum(appeal.status == "approved" for appeal in decided_appeals)
    overridden_reviews = 0
    for review in reviews:
        final_as_system = {
            "allow": "publish",
            "maintain_limit": "limit",
            "need_more_context": "manual_review",
        }.get(review.final_decision, review.final_decision)
        overridden_reviews += final_as_system != review.original_decision

    now = datetime.now(timezone.utc)
    trend = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        trend.append({
            "date": day.isoformat(),
            "submissions": sum(item.created_at.date() == day for item in contents),
            "manualReviews": sum(item.created_at.date() == day for item in reviews),
        })

    risk_distribution = Counter(f"L{record.risk_level}" for record in latest_records)
    decision_distribution = Counter(record.system_decision for record in latest_records)
    divergent_count = sum(item.divergent for item in comparisons)
    active_rule = get_active_rule_config(db)
    db.commit()
    return {
        "summary": {
            "totalContents": len(contents),
            "publicContents": sum(item.visible_to_public for item in contents),
            "pendingManualReview": sum(item.status in {"pending_manual_review", "need_more_context"} for item in contents),
            "limitedContents": sum(item.status in {"limited", "appeal_rejected"} for item in contents),
            "totalAppeals": len(appeals),
            "pendingAppeals": sum(item.status in {"submitted", "reviewing", "need_more_context"} for item in appeals),
            "appealApprovalRate": percentage(approved_appeals, len(decided_appeals)),
            "manualReviews": len(reviews),
            "manualOverrides": overridden_reviews,
            "manualOverrideRate": percentage(overridden_reviews, len(reviews)),
            "dualReviews": len(comparisons),
            "dualDivergences": divergent_count,
            "dualDivergenceRate": percentage(divergent_count, len(comparisons)),
        },
        "riskLevelDistribution": [
            {"name": f"L{level}", "count": risk_distribution.get(f"L{level}", 0)} for level in range(4)
        ],
        "systemDecisionDistribution": [
            {"name": name, "count": decision_distribution.get(name, 0)}
            for name in ["publish", "warn", "manual_review", "limit"]
        ],
        "last7Days": trend,
        "runtime": {
            "ruleVersion": active_rule.version,
            "primaryProvider": moderation_service.provider.name,
            "primaryModel": moderation_service.provider.model_version,
            "secondaryProvider": moderation_service.secondary_provider.name if moderation_service.secondary_provider else None,
            "secondaryModel": moderation_service.secondary_provider.model_version if moderation_service.secondary_provider else None,
            "dualReviewEnabled": moderation_service.secondary_provider is not None,
        },
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
    }
