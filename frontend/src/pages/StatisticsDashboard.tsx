import { AreaChartOutlined, AuditOutlined, FileProtectOutlined, RobotOutlined } from "@ant-design/icons";
import { Alert, Card, Col, Progress, Row, Skeleton, Space, Statistic, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useEffect, useMemo, useState } from "react";
import { getModerationStatistics } from "../api";
import { apiErrorMessage } from "../api/client";
import type { ModerationStatistics } from "../types";

const decisionLabels: Record<string, string> = {
  publish: "公开",
  warn: "公开并提醒",
  manual_review: "人工复核",
  limit: "限制",
};

function BarList({ items, labels }: { items: Array<{ name: string; count: number }>; labels?: Record<string, string> }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  return <div className="metric-bars">{items.map((item) => <div className="metric-bar" key={item.name}>
    <span>{labels?.[item.name] ?? item.name}</span>
    <div><i style={{ width: `${item.count * 100 / max}%` }} /></div>
    <strong>{item.count}</strong>
  </div>)}</div>;
}

export function StatisticsDashboard() {
  const [data, setData] = useState<ModerationStatistics | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { getModerationStatistics().then(setData).catch((caught) => setError(apiErrorMessage(caught))); }, []);
  const maxTrend = useMemo(() => Math.max(1, ...(data?.last7Days.map((item) => item.submissions) ?? [1])), [data]);
  if (!data && !error) return <div className="page"><Skeleton active /></div>;
  if (!data) return <div className="page"><Alert type="error" showIcon message="统计数据加载失败" description={error} /></div>;
  const { summary } = data;
  return <div className="page statistics-page">
    <section className="page-heading"><div><Typography.Title level={2}>审核数据统计看板</Typography.Title><Typography.Paragraph type="secondary">实时汇总内容流转、人工改判和双模型分歧，统计只用于运营观察，不替代个案判断。</Typography.Paragraph></div><Space wrap><Tag color="blue">规则 {data.runtime.ruleVersion}</Tag><Tag color={data.runtime.dualReviewEnabled ? "green" : "default"}>{data.runtime.dualReviewEnabled ? "双模型已启用" : "单模型模式"}</Tag></Space></section>
    <Row gutter={[16, 16]} className="statistics-cards">
      <Col xs={12} lg={6}><Card><Statistic title="内容总量" value={summary.totalContents} prefix={<FileProtectOutlined />} /><small>公开 {summary.publicContents} · 待复核 {summary.pendingManualReview} · 受限 {summary.limitedContents}</small></Card></Col>
      <Col xs={12} lg={6}><Card><Statistic title="申诉通过率" value={summary.appealApprovalRate} suffix="%" prefix={<AuditOutlined />} /><small>申诉 {summary.totalAppeals} · 待处理 {summary.pendingAppeals}</small></Card></Col>
      <Col xs={12} lg={6}><Card><Statistic title="人工改判率" value={summary.manualOverrideRate} suffix="%" prefix={<AreaChartOutlined />} /><small>复核 {summary.manualReviews} · 改判 {summary.manualOverrides}</small></Card></Col>
      <Col xs={12} lg={6}><Card><Statistic title="双模型分歧率" value={summary.dualDivergenceRate} suffix="%" prefix={<RobotOutlined />} /><small>比较 {summary.dualReviews} · 分歧 {summary.dualDivergences}</small></Card></Col>
    </Row>
    <div className="statistics-grid">
      <Card title="风险等级分布"><BarList items={data.riskLevelDistribution} /></Card>
      <Card title="系统最终分流"><BarList items={data.systemDecisionDistribution} labels={decisionLabels} /></Card>
      <Card title="最近 7 天内容提交" className="trend-card"><div className="trend-bars">{data.last7Days.map((item) => <div key={item.date}><strong>{item.submissions}</strong><Progress type="dashboard" percent={item.submissions * 100 / maxTrend} size={64} showInfo={false} strokeColor="#3154a5" /><span>{dayjs(item.date).format("MM-DD")}</span><small>复核 {item.manualReviews}</small></div>)}</div></Card>
      <Card title="当前审核运行配置"><div className="runtime-list"><span>主模型<strong>{data.runtime.primaryProvider} / {data.runtime.primaryModel}</strong></span><span>辅助模型<strong>{data.runtime.secondaryModel ? `${data.runtime.secondaryProvider} / ${data.runtime.secondaryModel}` : "未启用"}</strong></span><span>规则版本<strong>{data.runtime.ruleVersion}</strong></span><span>统计时间<strong>{dayjs(data.generatedAt).format("YYYY-MM-DD HH:mm:ss")}</strong></span></div></Card>
    </div>
  </div>;
}
