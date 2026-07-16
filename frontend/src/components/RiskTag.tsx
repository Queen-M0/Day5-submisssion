import { Tag } from "antd";

const riskLabels: Record<string, string> = {
  insult: "辱骂",
  harassment: "骚扰",
  implicit_attack: "隐晦攻击",
  discrimination: "歧视",
  threat: "威胁",
  fraud: "诈骗",
  privacy: "隐私",
  safe_context: "安全语境",
  repeated_targeting: "持续针对",
  group_pressure: "群体施压",
  quote: "引用语境",
  counter_speech: "反对攻击",
};

export function RiskTag({ type }: { type: string }) {
  return <Tag color={type === "safe_context" ? "success" : "volcano"}>{riskLabels[type] ?? type}</Tag>;
}

export function RiskLevelTag({ level }: { level: number }) {
  const values = [
    { color: "success", label: "L0 安全" },
    { color: "gold", label: "L1 低风险" },
    { color: "orange", label: "L2 中风险" },
    { color: "red", label: "L3 高风险" },
  ];
  const item = values[level] ?? values[0];
  return <Tag color={item.color}>{item.label}</Tag>;
}

