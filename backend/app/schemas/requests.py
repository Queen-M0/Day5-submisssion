from typing import Optional

from pydantic import Field

from app.schemas.common import APIModel


class CreateContentRequest(APIModel):
    scene_id: str
    content_type: str = "forum_reply"
    parent_id: Optional[str] = None
    text: str = Field(min_length=1, max_length=2000)


class SubmitAppealRequest(APIModel):
    appeal_type: str = "other"
    reason: str = Field(min_length=5, max_length=1000)


class ReviewDecisionRequest(APIModel):
    final_decision: str
    final_risk_level: int = Field(ge=0, le=3)
    review_reason: str = Field(min_length=5, max_length=1000)
    correction_type: str = "correct"

