from typing import Any, Dict, List

from app.providers.ai_provider import AppealCriticInput, AppealCriticProvider
from app.providers.openai_compat import call_openai_json
from app.schemas.common import AppealCriticResult


SYSTEM_PROMPT = """你是社区申诉复核的"反证 Agent"。你的任务不是做最终裁决，而是**主动挑战第一次审核判断**，为人工审核员提供独立参考。

你必须严格只输出一个 JSON 对象，不要输出解释、markdown 或代码块，字段如下（全部必填）：
{
  "upholdsInitial": bool,                 // 综合看来是否支持维持初次审核结论
  "recommendedDecision": "uphold" | "overturn_allow" | "overturn_limit" | "need_manual",
  "confidence": 0-1 小数,
  "riskLevel": 0|1|2|3,
  "riskScore": 0-100 整数,
  "riskTypes": [字符串],
  "supportsOriginalDecision": [字符串],   // 支持"维持原判"的论据，每条 <= 60 字
  "supportsChange": [字符串],             // 支持"改判"的论据（如补充上下文说明是台词/引用/误判），每条 <= 60 字
  "newEvidenceImpact": "补充上下文/申诉理由对风险判断的影响说明（1-2 句）",
  "remainingUncertainties": [字符串],     // 仍无法确定的点
  "evidence": [
    {"contentId": "证据所在楼层 id", "text": "从该楼层原文逐字摘录的片段", "reason": "为何支持你的判断", "riskType": "风险类型"}
  ],
  "reviewSuggestion": "给审核员的明确建议（如：建议改判允许 / 建议维持限制 / 信息不足建议补充）",
  "reasoning": "你的综合推理过程"
}

规则：
- 你是"反证"角色：应主动从申诉方角度寻找能推翻原判的依据，但最终要客观，不支持无依据的翻案。
- supportsOriginalDecision 与 supportsChange 必须都是字符串数组，至少各 1 条（若确实没有则给空数组）。
- recommendedDecision 含义：uphold=维持原判；overturn_allow=建议改判允许公开；overturn_limit=建议改判限制；need_manual=信息不足交人工。
- evidence.text 必须逐字来自下文提供的某条楼层原文，禁止编造或改写；contentId 必须是下文出现过的楼层 id。
- 若无法定位真实证据，请把 evidence 设为空数组，并适当降低 confidence。
"""


class RealAppealCriticProvider(AppealCriticProvider):
    """Appeal critic backed by an OpenAI-compatible chat API (Xiaomi MiMo)."""

    name = "real-appeal-critic"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        prompt_version: str,
        rule_version: str,
        timeout: float = 12.0,
        temperature: float = 0.0,
        max_tokens: int = 900,
    ):
        if not api_key:
            raise ValueError("RealAppealCriticProvider requires a non-empty api_key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_version = prompt_version
        self.appeal_prompt_version = prompt_version
        self.model_version = model
        self.rule_version = rule_version
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    def critique(self, payload: AppealCriticInput) -> AppealCriticResult:
        raw = call_openai_json(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=self._build_user_prompt(payload),
            timeout=self.timeout,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        parsed = self._coerce(raw)
        return AppealCriticResult.model_validate(parsed)

    @staticmethod
    def _build_user_prompt(payload: AppealCriticInput) -> str:
        init = payload.initial_review
        lines: List[str] = [
            "【被申诉内容】",
            f"- [contentId={payload.content_id}] 作者 {payload.author_name}（{payload.author_id}）：{payload.text}",
            "",
            "【初次审核结论（必须基于它做反证，不要凭空判断）】",
            f"- 系统分流 systemDecision={init.system_decision}，AI 建议 decision={init.decision}",
            f"- 风险等级 riskLevel={init.risk_level}，风险分 riskScore={init.risk_score}，置信度 confidence={init.confidence}",
            f"- 风险类型 riskTypes={', '.join(init.risk_types) or '（无）'}",
            f"- 对用户的说明：{init.user_visible_reason}",
            f"- 对审核员的说明：{init.reviewer_reason}",
        ]
        if init.evidence:
            lines.append("- 初次审核证据：")
            for ev in init.evidence:
                lines.append(f"  · [{ev.get('contentId', '?')}] {ev.get('quote', '')} —— {ev.get('reason', '')}")
        lines += [
            "",
            "【用户申诉】",
            f"- 申诉类型 appealType={payload.appeal_type}",
            f"- 申诉理由：{payload.appeal_reason}",
            f"- 补充上下文：{payload.extra_context or '（无）'}",
        ]
        if payload.parent_text is not None:
            lines += ["", f"【被回复楼层 contentId={payload.parent_id}】{payload.parent_text}"]
        if payload.context_messages:
            lines += ["", "【相关上下文楼层（可用于引用证据）】"]
            for msg in payload.context_messages:
                lines.append(f"- [contentId={msg.id}] {msg.author_name}（{msg.author_id}）：{msg.text}")
        lines += ["", "请作为反证 Agent 输出规定 JSON，主动从申诉方角度寻找可推翻原判的依据，但保持客观。"]
        return "\n".join(lines)

    @staticmethod
    def _coerce(parsed: Dict[str, Any]) -> Dict[str, Any]:
        decision_map = {
            "uphold": "uphold",
            "maintain": "uphold",
            "keep": "uphold",
            "sustain": "uphold",
            "support": "uphold",
            "overturn": "overturn_allow",
            "overturn_allow": "overturn_allow",
            "allow": "overturn_allow",
            "publish": "overturn_allow",
            "reverse_allow": "overturn_allow",
            "overturn_limit": "overturn_limit",
            "limit": "overturn_limit",
            "restrict": "overturn_limit",
            "need_manual": "need_manual",
            "manual": "need_manual",
            "escalate": "need_manual",
            "more_context": "need_manual",
            "need_more_context": "need_manual",
        }
        decision = str(parsed.get("recommendedDecision", "need_manual")).strip().lower()
        parsed["recommendedDecision"] = decision_map.get(decision, "need_manual")
        # Keep upholdsInitial consistent with the recommended decision.
        parsed["upholdsInitial"] = parsed["recommendedDecision"] == "uphold"

        def clamp(value, low, high, default):
            try:
                num = type(default)(value)
            except (TypeError, ValueError):
                return default
            return max(low, min(high, num))

        parsed["riskLevel"] = clamp(parsed.get("riskLevel", 0), 0, 3, 0)
        parsed["riskScore"] = clamp(parsed.get("riskScore", 0), 0, 100, 0)
        parsed["confidence"] = clamp(parsed.get("confidence", 0.0), 0.0, 1.0, 0.0)
        for key in ("riskTypes", "supportsOriginalDecision", "supportsChange", "remainingUncertainties", "evidence"):
            if not isinstance(parsed.get(key), list):
                parsed[key] = []
        for key in ("newEvidenceImpact", "reviewSuggestion", "reasoning"):
            parsed.setdefault(key, "")
        return parsed
