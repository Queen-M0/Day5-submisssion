import { ArrowRightOutlined, InboxOutlined, ReloadOutlined } from "@ant-design/icons";
import { App, Button, Empty, List, Space, Spin, Statistic, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getReviewTasks } from "../api";
import { RiskLevelTag, RiskTag } from "../components/RiskTag";
import type { ReviewTask } from "../types";

export function ReviewerDashboard() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try { setTasks(await getReviewTasks()); }
    catch { message.error("审核任务加载失败，请确认当前身份具有审核权限"); }
    finally { setLoading(false); }
  }, [message]);
  useEffect(() => { void load(); }, [load]);

  const stats = useMemo(() => ({
    total: tasks.length,
    appeals: tasks.filter((item) => item.hasAppeal).length,
    high: tasks.filter((item) => item.riskLevel >= 3).length,
  }), [tasks]);

  return (
    <div className="page reviewer-page">
      <section className="page-heading">
        <div>
          <Typography.Title level={2}>审核工作台</Typography.Title>
          <Typography.Paragraph type="secondary">集中处理复杂语境与用户申诉，人工结论将覆盖系统初判。</Typography.Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => void load()}>刷新队列</Button>
      </section>
      <section className="stats-band">
        <Statistic title="待处理" value={stats.total} />
        <Statistic title="用户申诉" value={stats.appeals} />
        <Statistic title="高风险" value={stats.high} />
        <Statistic title="当前 Provider" value="Mock AI" valueStyle={{ fontSize: 20 }} />
      </section>
      <section className="review-queue">
        <div className="section-title-row">
          <Typography.Title level={4}>待复核队列</Typography.Title>
          <Typography.Text type="secondary">按进入队列时间排序</Typography.Text>
        </div>
        <Spin spinning={loading}>
          {tasks.length === 0 ? <Empty image={<InboxOutlined className="large-empty-icon" />} description="当前没有待处理任务" /> : (
            <List
              dataSource={tasks}
              renderItem={(task) => (
                <List.Item className="task-row" onClick={() => navigate(`/reviewer/${task.taskId}`)}>
                  <div className="task-risk"><RiskLevelTag level={task.riskLevel} /></div>
                  <div className="task-main">
                    <div className="task-topline">
                      <Space wrap>
                        <Typography.Text strong>{task.authorName}</Typography.Text>
                        {task.hasAppeal && <Tag color="blue">用户申诉</Tag>}
                        {task.riskTypes.map((type) => <RiskTag key={type} type={type} />)}
                      </Space>
                      <Typography.Text type="secondary">{dayjs(task.createdAt).format("MM-DD HH:mm")}</Typography.Text>
                    </div>
                    <Typography.Paragraph className="task-content" ellipsis={{ rows: 2 }}>{task.contentText}</Typography.Paragraph>
                    <Typography.Text type="secondary">{task.summary}</Typography.Text>
                  </div>
                  <Button type="text" icon={<ArrowRightOutlined />} aria-label="进入复核详情" />
                </List.Item>
              )}
            />
          )}
        </Spin>
      </section>
    </div>
  );
}
