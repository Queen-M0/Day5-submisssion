import { ExclamationCircleOutlined, RobotOutlined } from "@ant-design/icons";
import { Alert, Space, Tag, Typography } from "antd";
import type { DualReviewComparison } from "../types";

const decisionText: Record<string, string> = {
  publish: "建议公开",
  warn: "公开并提醒",
  manual_review: "建议人工复核",
  limit: "建议限制",
  error: "调用失败",
};

export function DualReviewPanel({ value, compact = false }: { value?: DualReviewComparison | null; compact?: boolean }) {
  if (!value) return <Alert type="info" showIcon message="本次审核未启用双模型复核" />;
  return <div className={`dual-review-box ${value.divergent ? "divergent" : ""}`}>
    <Space wrap><RobotOutlined /><Typography.Text strong>双模型独立复核</Typography.Text><Tag color={value.divergent ? "volcano" : "green"}>{value.divergent ? "存在分歧" : "结论一致"}</Tag><Tag>系统：{value.systemResolution}</Tag></Space>
    {!compact && <div className="dual-model-grid">
      <div><span>主模型</span><strong>{value.primary.modelVersion}</strong><small>{decisionText[value.primary.decision] ?? value.primary.decision} · L{value.primary.riskLevel} · {value.primary.riskTypes.join("、") || "无风险"}</small></div>
      <div><span>辅助模型</span><strong>{value.secondary.modelVersion}</strong><small>{decisionText[value.secondary.decision] ?? value.secondary.decision} · L{value.secondary.riskLevel} · {value.secondary.riskTypes.join("、") || "无风险"}</small></div>
    </div>}
    {value.reasons.length > 0 && <Alert className="dual-review-reasons" type="warning" showIcon icon={<ExclamationCircleOutlined />} message="转人工原因" description={value.reasons.join("；")} />}
    {value.failureReason && <Alert type="error" showIcon message="辅助模型调用失败，已安全降级" description={value.failureReason} />}
  </div>;
}
