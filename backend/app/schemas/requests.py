from typing import List, Literal, Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel


class CreateContentRequest(APIModel):
    scene_id: str
    content_type: str = "forum_reply"
    parent_id: Optional[str] = None
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class CreateTopicRequest(APIModel):
    title: str = Field(min_length=4, max_length=120)
    category: str = Field(min_length=1, max_length=40)
    body: str = Field(min_length=5, max_length=2000)

    @field_validator("title", "category", "body")
    @classmethod
    def validate_topic_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空")
        return value

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        if len(value) < 4:
            raise ValueError("话题标题至少 4 个字符")
        return value

    @field_validator("body")
    @classmethod
    def validate_body_length(cls, value: str) -> str:
        if len(value) < 5:
            raise ValueError("话题正文至少 5 个字符")
        return value


class CreateTopicContentRequest(APIModel):
    text: str = Field(min_length=1, max_length=2000)
    reply_to_content_id: Optional[str] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class SubmitAppealRequest(APIModel):
    appeal_type: str = "other"
    reason: str = Field(min_length=5, max_length=1000)
    extra_context: str = Field(default="", max_length=2000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("申诉理由至少 5 个字符")
        return value


class LoginRequest(APIModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class AppealSupplementRequest(APIModel):
    extra_context: str = Field(min_length=5, max_length=2000)

    @field_validator("extra_context")
    @classmethod
    def validate_extra_context(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("补充上下文至少 5 个字符")
        return value


class ReviewDecisionRequest(APIModel):
    final_decision: Literal["allow", "maintain_limit", "need_more_context"]
    final_risk_level: Optional[int] = Field(default=None, ge=0, le=3)
    review_reason: str = Field(min_length=5, max_length=1000)
    correction_type: Optional[str] = None

    @field_validator("review_reason")
    @classmethod
    def validate_review_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("复核理由至少 5 个字符")
        return value


class UpdateModerationRulesRequest(APIModel):
    name: str = Field(min_length=2, max_length=80)
    enabled_risk_types: List[str] = Field(min_length=1)
    auto_limit_min_risk_level: int = Field(ge=1, le=3)
    manual_review_min_risk_level: int = Field(ge=1, le=3)
    min_confidence: float = Field(ge=0, le=1)
    require_grounded_evidence: bool = True
    route_divergence_to_manual: bool = True
    change_reason: str = Field(min_length=5, max_length=500)

    @field_validator("enabled_risk_types")
    @classmethod
    def validate_risk_types(cls, value: List[str]) -> List[str]:
        allowed = {"insult", "harassment", "threat", "fraud", "discrimination", "implicit_attack"}
        invalid = set(value) - allowed
        if invalid:
            raise ValueError(f"不支持的风险类型: {', '.join(sorted(invalid))}")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.manual_review_min_risk_level > self.auto_limit_min_risk_level:
            raise ValueError("人工复核阈值不能高于自动限制阈值")
        return self
