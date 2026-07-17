import { ArrowRightOutlined, ExclamationCircleOutlined, InboxOutlined, RobotOutlined, SafetyCertificateOutlined, UserSwitchOutlined } from "@ant-design/icons";
import { Button, Card, Empty, Progress, Segmented, Space, Statistic, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RiskLevelTag, RiskTag } from "../components/RiskTag";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";

export function ReviewerDashboard() {
  const navigate = useNavigate();
  const { users } = useAuth();
  const { reviewTasks, findFloor, findAppeal } = useDemo();
  const [filter, setFilter] = useState("全部任务");
  const pending = reviewTasks.filter((task) => task.status === "pending");
  const tasks = filter === "用户申诉" ? pending.filter((task) => task.source === "user_appeal") : filter === "AI 转人工" ? pending.filter((task) => task.source === "ai_escalation") : filter === "模型分歧" ? pending.filter((task) => task.dualReviewDivergent) : pending;
  const stats = useMemo(() => ({ appeals: pending.filter((item) => item.source === "user_appeal").length, escalations: pending.filter((item) => item.source === "ai_escalation").length, divergent: pending.filter((item) => item.dualReviewDivergent).length }), [pending]);
  const userName = (id: string) => users.find((item) => item.id === id)?.displayName ?? "社区用户";

  return <div className="page reviewer-dashboard-page">
    <section className="reviewer-hero"><div><Space className="eyebrow"><SafetyCertificateOutlined /> HUMAN IN THE LOOP</Space><Typography.Title level={2}>人工审核工作台</Typography.Title><Typography.Paragraph>同时查看原始上下文、AI 证据和用户申诉。AI 只提供分析，最终决定必须由审核员填写具体理由。</Typography.Paragraph></div><div className="reviewer-duty"><strong>今日复核原则</strong><span>先确认说话者与对象，再判断意图；上下文不足时不武断裁决。</span></div></section>
    <section className="reviewer-stats">
      <Statistic title="待复核总数" value={pending.length} prefix={<InboxOutlined />} />
      <Statistic title="用户申诉" value={stats.appeals} prefix={<UserSwitchOutlined />} />
      <Statistic title="AI 主动转人工" value={stats.escalations} prefix={<RobotOutlined />} />
      <Statistic title="双模型分歧" value={stats.divergent} prefix={<ExclamationCircleOutlined />} />
    </section>
    <div className="queue-toolbar"><div><Typography.Title level={3}>待复核队列</Typography.Title><Typography.Text type="secondary">申诉优先，其次按进入队列时间排序</Typography.Text></div><Segmented value={filter} onChange={(value) => setFilter(String(value))} options={["全部任务", "用户申诉", "AI 转人工", "模型分歧"]} /></div>
    {tasks.length === 0 ? <Empty image={<InboxOutlined className="large-empty-icon" />} description="当前筛选下没有待处理任务" /> : <div className="review-task-grid">
      {tasks.map((task) => {
        const found = findFloor(task.contentId);
        if (!found) return null;
        const { floor, topic } = found;
        const appeal = findAppeal(floor.id);
        return <Card key={task.id} className={`review-task-card priority-${task.priority}`} hoverable onClick={() => navigate(`/reviewer/${task.id}`)}>
          <div className="task-card-head"><Space><Tag color={task.source === "user_appeal" ? "blue" : "gold"}>{task.source === "user_appeal" ? "用户申诉" : "AI 主动转人工"}</Tag>{task.priority === "high" && <Tag color="red">优先处理</Tag>}{task.dualReviewDivergent && <Tag color="volcano">双模型分歧</Tag>}</Space><Typography.Text type="secondary">等待 {dayjs().diff(dayjs(task.createdAt), "minute")} 分钟</Typography.Text></div>
          <Typography.Text type="secondary">{topic.title}</Typography.Text>
          <Typography.Paragraph className="task-quote" ellipsis={{ rows: 2 }}>“{floor.text}”</Typography.Paragraph>
          <div className="task-author-row"><span>发布者：<strong>{userName(floor.authorId)}</strong></span><span>{dayjs(floor.createdAt).format("MM-DD HH:mm")}</span></div>
          <div className="risk-line"><RiskLevelTag level={floor.moderation.riskLevel} /><Progress percent={floor.moderation.riskScore} showInfo={false} strokeColor={floor.moderation.riskLevel >= 3 ? "#c2413b" : "#c98322"} /></div>
          <Space wrap>{floor.moderation.riskTypes.map((type) => <RiskTag key={type} type={type} />)}{floor.moderation.contextTags.map((type) => <RiskTag key={type} type={type} />)}</Space>
          {appeal && <div className="appeal-preview"><span>申诉重点</span><p>{appeal.reason}</p></div>}
          <div className="task-card-footer"><span>{floor.moderation.evidence.length} 条证据 · {floor.moderation.contextUsed.length} 类上下文</span><Button type="primary" ghost icon={<ArrowRightOutlined />}>进入复核</Button></div>
        </Card>;
      })}
    </div>}
  </div>;
}
