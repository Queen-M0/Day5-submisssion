import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined, EyeInvisibleOutlined } from "@ant-design/icons";
import { Tag } from "antd";

const statusMap: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
  pending_ai_review: { color: "processing", label: "AI 审核中", icon: <ClockCircleOutlined /> },
  published: { color: "success", label: "已发布", icon: <CheckCircleOutlined /> },
  limited: { color: "error", label: "已限制", icon: <EyeInvisibleOutlined /> },
  pending_manual_review: { color: "warning", label: "待人工复核", icon: <ClockCircleOutlined /> },
  appeal_submitted: { color: "processing", label: "申诉已提交", icon: <ClockCircleOutlined /> },
  appeal_reviewing: { color: "processing", label: "申诉复核中", icon: <ClockCircleOutlined /> },
  appeal_approved: { color: "success", label: "申诉通过", icon: <CheckCircleOutlined /> },
  appeal_rejected: { color: "error", label: "申诉驳回", icon: <CloseCircleOutlined /> },
  need_more_context: { color: "warning", label: "待补充上下文", icon: <ClockCircleOutlined /> },
};

export function StatusTag({ status }: { status: string }) {
  const config = statusMap[status] ?? { color: "default", label: status, icon: null };
  return (
    <Tag color={config.color} icon={config.icon}>
      {config.label}
    </Tag>
  );
}

