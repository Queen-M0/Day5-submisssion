from typing import Literal, Optional

from pydantic import Field, field_validator

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
