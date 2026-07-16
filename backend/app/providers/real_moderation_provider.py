from typing import Any, Dict, List

from app.providers.ai_provider import ModerationInput, ModerationProvider
from app.providers.openai_compat import call_openai_json
from app.schemas.common import ModerationResult


SYSTEM_PROMPT = """你是社区文字内容审核分析引擎，负责对"当前待审核内容"结合上下文做语义风险判断。

你必须严格只输出一个 JSON 对象，不要输出解释、markdown 或代码块，字段如下（全部必填）：
{
  "isViolation": bool,
  "riskLevel": 0|1|2|3,
  "riskScore": 0-100 整数,
  "riskTypes": [字符串],           // 如 harassment/threat/fraud/insult/implicit_attack/safe_context
  "confidence": 0-1 小数,
  "decision": "publish" | "manual_review" | "limit",
  "targetUsers": [被指向用户的 authorId],
  "isQuoteOrReport": bool,          // 是否为引用/转述/举报语境
  "quoteContextSafe": bool,         // 引用是否属于反对/举报等安全语境
  "hasImplicitAttack": bool,        // 是否含反讽/外号/暗示性攻击
  "hasContinuousHarassment": bool,  // 是否对同一对象连续针对
  "evidence": [
    {"contentId": "证据所在楼层的 id", "text": "从该楼层原文逐字摘录的片段", "reason": "为何构成风险", "riskType": "风险类型"}
  ],
  "contextReasoning": "结合上下文的判断理由",
  "userVisibleReason": "给普通用户看的简短说明",
  "reviewerReason": "给审核员看的详细说明",
  "suggestedRevision": "若被限制给出的修改建议，否则空字符串"
}

判定规则：
- decision 只能是 publish / manual_review / limit 三选一。
- 明确的辱骂、威胁、诈骗、直接人身攻击 -> riskLevel 3 且 decision=limit。
- 反讽、外号、暗示性攻击、连续针对但无明显敏感词 -> riskLevel 2 且 decision=manual_review。
- 引用他人不当言论用于反对/举报，且作者本人未认同攻击 -> 视为安全语境，decision=publish。
- 无明显风险 -> riskLevel 0 且 decision=publish。
- evidence.text 必须逐字来自下文提供的某条楼层原文，禁止编造或改写；contentId 必须是下文出现过的楼层 id。
- 若无法定位真实证据，请把 evidence 设为空数组，并适当降低 confidence。
"""


class RealModerationProvider(ModerationProvider):
    """Moderation provider backed by an OpenAI-compatible chat API (Xiaomi MiMo)."""

    name = "real-moderation"

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
            raise ValueError("RealModerationProvider requires a non-empty api_key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt_version = prompt_version
        self.model_version = model
        self.rule_version = rule_version
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    def moderate(self, payload: ModerationInput) -> ModerationResult:
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
        return ModerationResult.model_validate(parsed)

    @staticmethod
    def _build_user_prompt(payload: ModerationInput) -> str:
        lines: List[str] = [f"话题标题：{payload.topic_title or '（无）'}", ""]
        if payload.messages:
            lines.append("最近公开楼层（按时间顺序，contentId 可用于引用证据）：")
            for msg in payload.messages:
                lines.append(f"- [contentId={msg.id}] {msg.author_name}（{msg.author_id}）：{msg.text}")
            lines.append("")
        if payload.parent_text is not None:
            lines.append(
                f"被回复楼层 [contentId={payload.parent_id}] "
                f"作者={payload.parent_author_id}：{payload.parent_text}"
            )
            lines.append("")
        lines.append("当前待审核内容：")
        lines.append(
            f"- [contentId={payload.content_id}] 作者 {payload.author_name}"
            f"（{payload.author_id}）：{payload.text}"
        )
        lines.append("")
        lines.append("请对上面【当前待审核内容】做判断，并只输出规定的 JSON 对象。")
        return "\n".join(lines)

    @staticmethod
    def _coerce(parsed: Dict[str, Any]) -> Dict[str, Any]:
        decision_map = {
            "allow": "publish",
            "approve": "publish",
            "pass": "publish",
            "block": "limit",
            "reject": "limit",
            "review": "manual_review",
            "escalate": "manual_review",
        }
        decision = str(parsed.get("decision", "manual_review")).strip().lower()
        parsed["decision"] = decision_map.get(decision, decision)

        def clamp(value, low, high, default):
            try:
                num = type(default)(value)
            except (TypeError, ValueError):
                return default
            return max(low, min(high, num))

        parsed["riskLevel"] = clamp(parsed.get("riskLevel", 0), 0, 3, 0)
        parsed["riskScore"] = clamp(parsed.get("riskScore", 0), 0, 100, 0)
        parsed["confidence"] = clamp(parsed.get("confidence", 0.0), 0.0, 1.0, 0.0)
        parsed.setdefault("isViolation", parsed["riskLevel"] > 0)
        for key in ("riskTypes", "targetUsers", "evidence"):
            if not isinstance(parsed.get(key), list):
                parsed[key] = []
        for key in ("contextReasoning", "userVisibleReason", "reviewerReason"):
            parsed.setdefault(key, "")
        parsed.setdefault("suggestedRevision", "")
        return parsed
