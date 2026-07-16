from app.providers.ai_provider import AppealCriticInput, AppealCriticProvider
from app.schemas.common import AppealCriticResult


class MockAppealCriticProvider(AppealCriticProvider):
    """Deterministic, offline appeal critic for demos and regression tests.

    The logic deliberately mirrors the real provider's contract: it consumes
    the initial moderation record and produces two-sided arguments plus a
    non-binding recommendation, without making the final decision.
    """

    name = "mock-appeal-critic"
    prompt_version = "mock-appeal-v1"
    model_version = "mock-rules-v1"
    rule_version = "appeal-community-v1"

    _SUGGESTIONS = {
        "uphold": "建议维持限制，初次审核证据充分。",
        "overturn_allow": "建议改判允许，结合补充上下文重新判断。",
        "overturn_limit": "建议改判为限制处理。",
        "need_manual": "信息不足，建议要求补充上下文或人工复核。",
    }

    def critique(self, payload: AppealCriticInput) -> AppealCriticResult:
        init = payload.initial_review
        extra = (payload.extra_context or "").strip()
        context_claim = bool(extra) or payload.appeal_type in (
            "missing_context",
            "misunderstanding",
            "quote_context",
        )
        serious = bool(init.risk_types) and init.risk_types[0] in ("threat", "fraud", "insult")

        if serious and not context_claim:
            decision = "uphold"
            supports_original = [
                f"初次审核判定为 {init.risk_types[0]}，风险等级 {init.risk_level}，证据明确。",
                "申诉未提供新的事实或上下文，无法推翻原判。",
            ]
            supports_change: list = []
            impact = "申诉未提供新的事实或上下文，无法推翻原判。"
            uncertainties: list = []
        elif serious and context_claim:
            decision = "overturn_allow"
            supports_change = [
                f"申诉补充上下文：{extra[:40] or '（补充语境）'}，可能改变风险性质。",
                "作者主张为引用 / 台词 / 误读，需人工结合全文判断。",
            ]
            supports_original = [
                f"原文仍含 {init.risk_types[0]} 类表述，存在客观风险点。",
            ]
            impact = "补充上下文可能说明该内容为引用或台词，但原文风险表述客观存在。"
            uncertainties = ["补充上下文是否足以改变定性需人工确认。"]
        else:
            decision = "need_manual"
            supports_original = [f"初次审核结论为 {init.system_decision}，存在不确定点。"]

            supports_change = []
            impact = "信息有限，建议人工结合上下文判断。"
            uncertainties = ["申诉理由与上下文是否足以改变定性尚不明确。"]

        return AppealCriticResult(
            upholds_initial=decision == "uphold",
            recommended_decision=decision,
            confidence=0.7 if decision != "need_manual" else 0.5,
            risk_level=init.risk_level,
            risk_score=init.risk_score,
            risk_types=list(init.risk_types),
            supports_original_decision=supports_original,
            supports_change=supports_change,
            new_evidence_impact=impact,
            remaining_uncertainties=uncertainties,
            evidence=[],
            review_suggestion=self._SUGGESTIONS[decision],
            reasoning="Mock 反证 Agent 基于规则生成（无真实 LLM 调用）。",
        )
