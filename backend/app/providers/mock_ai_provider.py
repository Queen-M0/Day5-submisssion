import re
from typing import List, Tuple

from app.providers.ai_provider import AppealInput, ModerationInput, ModerationProvider
from app.schemas.common import CounterAnalysisResult, EvidenceItem, ModerationResult


class MockAIProvider(ModerationProvider):
    """Deterministic provider for demos and regression tests."""

    name = "mock-ai"
    model_version = "mock-rules-v2"
    moderation_prompt_version = "mock-moderation-v2"
    appeal_prompt_version = "mock-appeal-critic-v1"

    safe_markers = ("不合适", "请管理员", "举报", "不要说", "不能说", "引用", "反对")
    quote_markers = ("引用", "他说", "楼上说", "有人说", "举报", "不要说", "这种话")
    insult_terms = ("废物", "垃圾", "蠢货", "没用", "什么货色")
    threat_terms = ("放学等着", "让你后悔", "弄死", "报复你")
    fraud_terms = ("私人账户", "统一转账", "取消资格", "验证码", "刷单返利")
    implicit_terms = ("大家都看看", "懂的都懂", "大聪明", "班级巨婴", "不点名", "装领导", "拖后腿")

    def moderate(self, payload: ModerationInput) -> ModerationResult:
        text = payload.text
        is_quote = any(marker in text for marker in self.quote_markers) or bool(re.search(r"[\u201c\u201d\"]", text))
        safe_quote = is_quote and any(marker in text for marker in self.safe_markers)
        endorses_attack = any(marker in text for marker in ("说得没错", "我也觉得", "确实是"))

        if safe_quote and not endorses_attack:
            return self._result(
                risk_level=0,
                score=10,
                risk_types=["safe_context"],
                decision="publish",
                confidence=0.91,
                evidence=[EvidenceItem(content_id=payload.content_id, text=self._first_match(text, self.safe_markers), reason="存在明确的引用、反驳或举报语境", risk_type="safe_context")],
                context_reasoning="内容虽然可能包含攻击性词语，但作者在引用并反对该表达。",
                user_reason="已识别为引用或举报语境，内容已发布。",
                reviewer_reason="Mock Provider 识别到安全语境标记，未将命中的攻击词直接判为违规。",
                is_quote=True,
                quote_safe=True,
            )

        high_type, high_term = self._match_high_risk(text)
        if high_type:
            reason_map = {
                "threat": "包含明确恐吓或报复表达",
                "fraud": "包含可疑转账或诱导信息",
                "insult": "包含直接针对他人的贬损表达",
            }
            return self._result(
                risk_level=3,
                score=90 if high_type != "insult" else 85,
                risk_types=[high_type],
                decision="limit",
                confidence=0.94,
                evidence=[EvidenceItem(content_id=payload.content_id, text=high_term, reason=reason_map[high_type], risk_type=high_type)],
                context_reasoning="当前内容包含明确且可定位的高风险证据。",
                user_reason="这条内容可能涉及针对他人的不友善或高风险表达，暂未公开。",
                reviewer_reason=f"命中 {high_type} 演示规则，证据片段为“{high_term}”。",
                is_quote=is_quote,
                quote_safe=False,
                suggested="请删除攻击、威胁或诱导性表达后重新发布。",
            )

        implicit = [term for term in self.implicit_terms if term in text]
        recent_same_author = [message for message in payload.messages[-5:] if message.author_id == payload.author_id]
        continuous = bool(implicit) and len(recent_same_author) >= 1
        if implicit:
            score = 74 if continuous else 65
            return self._result(
                risk_level=2,
                score=score,
                risk_types=["harassment", "implicit_attack"],
                decision="manual_review",
                confidence=0.78,
                evidence=[EvidenceItem(content_id=payload.content_id, text=term, reason="可能构成反讽、外号或暗示性攻击", risk_type="implicit_attack") for term in implicit[:2]],
                context_reasoning="表达未必含明显敏感词，但存在指向不清的反讽或暗示，需要结合上下文人工判断。",
                user_reason="内容可能涉及针对他人的暗示性评价，已进入人工复核。",
                reviewer_reason="请核对回复对象及同一作者近期发言，判断是否形成连续针对。",
                continuous=continuous,
                implicit=True,
                suggested="请聚焦具体事件，避免使用外号或暗示性评价。",
            )

        return self._result(
            risk_level=0,
            score=8,
            risk_types=[],
            decision="publish",
            confidence=0.96,
            evidence=[],
            context_reasoning="当前文本和可用上下文未发现明确风险证据。",
            user_reason="内容已发布。",
            reviewer_reason="Mock Provider 未命中高风险或复杂语境规则。",
        )

    def analyze_appeal(self, payload: AppealInput) -> CounterAnalysisResult:
        change_markers = ("引用", "台词", "举报", "反对", "缺少前文", "不是现实")
        combined = f"{payload.reason}\n{payload.extra_context}"
        supports_change = any(marker in combined for marker in change_markers)
        if supports_change:
            quote = next((marker for marker in change_markers if marker in combined), payload.reason[:20])
            source_id = "appeal-extra-context" if quote in payload.extra_context else "appeal-reason"
            return CounterAnalysisResult(
                supports_original_decision=["原文包含可能引发风险的直接表达，第一次限制具有安全依据。"],
                supports_change=["申诉补充了引用、台词或反对攻击的语境，第一次判断可能混淆了说话者归属。"],
                new_evidence_impact="新增上下文显著削弱原判，应由审核员核对后考虑改判。",
                remaining_uncertainties=["仍需人工确认补充上下文是否与原讨论一致。"],
                review_suggestion="allow",
                reviewer_summary="原判有表面文本依据，但申诉提供了足以挑战原判的新语境。",
                evidence=[EvidenceItem(content_id=source_id, text=quote, reason="申诉材料提供了可能改变说话者与意图判断的新信息", risk_type="counter_evidence")],
            )
        return CounterAnalysisResult(
            supports_original_decision=["申诉未提供足以推翻原始风险证据的新信息。"],
            supports_change=[],
            new_evidence_impact="新增信息对第一次判断影响有限。",
            remaining_uncertainties=["需要人工确认当事人关系和真实交流场景。"],
            review_suggestion="maintain_limit",
            reviewer_summary="当前材料更支持维持原判，但最终结果仍由人工决定。",
            evidence=[],
        )

    def _match_high_risk(self, text: str) -> Tuple[str, str]:
        for risk_type, terms in (
            ("threat", self.threat_terms),
            ("fraud", self.fraud_terms),
            ("insult", self.insult_terms),
        ):
            for term in terms:
                if term in text:
                    return risk_type, term
        return "", ""

    @staticmethod
    def _first_match(text: str, markers: Tuple[str, ...]) -> str:
        return next((marker for marker in markers if marker in text), text[:20])

    @staticmethod
    def _result(
        risk_level: int,
        score: int,
        risk_types: List[str],
        decision: str,
        confidence: float,
        evidence: List[EvidenceItem],
        context_reasoning: str,
        user_reason: str,
        reviewer_reason: str,
        is_quote: bool = False,
        quote_safe: bool = False,
        continuous: bool = False,
        implicit: bool = False,
        suggested: str = "",
    ) -> ModerationResult:
        return ModerationResult(
            is_violation=risk_level > 0,
            risk_level=risk_level,
            risk_score=score,
            risk_types=risk_types,
            confidence=confidence,
            decision=decision,
            is_quote_or_report=is_quote,
            quote_context_safe=quote_safe,
            has_implicit_attack=implicit,
            has_continuous_harassment=continuous,
            evidence=evidence,
            context_reasoning=context_reasoning,
            user_visible_reason=user_reason,
            reviewer_reason=reviewer_reason,
            suggested_revision=suggested,
        )
