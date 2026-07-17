import { CheckCircleOutlined, HistoryOutlined } from "@ant-design/icons";
import { Card, Empty, Space, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { StatusTag } from "../components/StatusTag";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";

export function ReviewHistoryPage() {
  const { users } = useAuth();
  const { reviewTasks, findFloor } = useDemo();
  const records = reviewTasks.filter((item) => item.status === "resolved").sort((a, b) => (b.resolvedAt ?? "").localeCompare(a.resolvedAt ?? ""));
  const userName = (id: string) => users.find((item) => item.id === id)?.displayName ?? "社区用户";
  return <div className="page review-history-page">
    <section className="page-heading"><div><Typography.Title level={2}>人工复核记录</Typography.Title><Typography.Paragraph type="secondary">原判、最终决定、具体理由和处理时间均保留，不覆盖原始 AI 记录。</Typography.Paragraph></div><div className="history-count"><HistoryOutlined /> {records.length} 条已完成</div></section>
    {records.length === 0 ? <Empty image={<HistoryOutlined className="large-empty-icon" />} description="还没有完成的复核；请先从待复核队列处理一个案例" /> : <div className="history-list">{records.map((task) => {
      const found = findFloor(task.contentId); if (!found) return null;
      const status = task.finalDecision === "allow" ? "appeal_approved" : task.finalDecision === "maintain_limit" ? "appeal_rejected" : "need_more_context";
      const finalText = task.finalDecision === "allow" ? "允许公开" : task.finalDecision === "maintain_limit" ? "维持限制" : "要求补充";
      return <Card key={task.id} className="history-card"><div className="history-card-head"><Space><CheckCircleOutlined className="history-check" /><StatusTag status={status} /><Tag>{task.source === "user_appeal" ? "申诉复核" : "主动复核"}</Tag>{task.wasOverridden && <Tag color="purple">人工改判</Tag>}</Space><Typography.Text type="secondary">{dayjs(task.resolvedAt).format("YYYY-MM-DD HH:mm")}</Typography.Text></div><Typography.Text type="secondary">{found.topic.title} · {userName(found.floor.authorId)}</Typography.Text><Typography.Title level={4}>“{found.floor.text}”</Typography.Title><div className="decision-compare"><div><span>AI 原始建议</span><strong>{task.originalSuggestedAction ?? found.floor.moderation.suggestedAction}</strong></div><div><span>规则系统分流</span><strong>{task.originalSystemDecision ?? found.floor.moderation.systemDecision}</strong></div><div><span>人工最终决定</span><strong>{finalText}</strong></div></div><div className="history-reason"><span>审核员理由</span><p>{task.reviewReason}</p></div></Card>;
    })}</div>}
  </div>;
}
