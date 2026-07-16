import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined, RobotOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Alert, App, Avatar, Button, Descriptions, Empty, Form, Input, Progress, Radio, Space, Tag, Timeline, Typography } from "antd";
import dayjs from "dayjs";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { RiskLevelTag, RiskTag } from "../components/RiskTag";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";
import { apiErrorMessage } from "../api/client";

export function ReviewDetailPage() {
  const { taskId = "" } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { users } = useAuth();
  const { reviewTasks, findFloor, findAppeal, resolveTask } = useDemo();
  const task = reviewTasks.find((item) => item.id === taskId);
  const found = task ? findFloor(task.contentId) : undefined;
  const appeal = found ? findAppeal(found.floor.id) : undefined;
  const [saving, setSaving] = useState(false);
  const userName = (id: string) => users.find((item) => item.id === id)?.displayName ?? "社区用户";

  if (!task || !found) return <div className="page"><Empty description="复核任务不存在"><Button onClick={() => navigate("/reviewer")}>返回队列</Button></Empty></div>;
  const { topic, floor } = found;
  const context = topic.floors.filter((item) => item.visibleToPublic || item.id === floor.id).slice(-5);
  const defaultDecision = appeal ? "allow" : "maintain_limit";

  const decide = async (values: { decision: "allow" | "maintain_limit" | "need_more_context"; reason: string }) => {
    setSaving(true);
    try {
      await resolveTask(task.id, values.decision, values.reason);
      message.success(values.decision === "allow" ? "已改判允许，内容已分配最新楼层并公开" : "人工复核结论已保存");
      navigate("/reviewer/history");
    } catch (error) {
      message.error(apiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  return <div className="review-workspace-page">
    <header className="workspace-header"><Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/reviewer")}>返回队列</Button><div><Typography.Text type="secondary">{topic.title}</Typography.Text><Typography.Title level={3}>复核任务 · {task.source === "user_appeal" ? "用户申诉" : "AI 主动转人工"}</Typography.Title></div><Space><Tag color={task.priority === "high" ? "red" : "gold"}>{task.priority === "high" ? "高优先级" : "普通优先级"}</Tag><Tag>{task.id}</Tag></Space></header>
    <div className="review-workspace-grid">
      <section className="workspace-panel context-panel">
        <div className="workspace-panel-title"><span>01</span><div><strong>原始上下文</strong><small>最近 5 楼与回复关系</small></div></div>
        <div className="current-content-box"><span>当前待复核内容 · {userName(floor.authorId)}</span><p>{floor.text}</p></div>
        <Timeline items={context.map((item) => ({ color: item.id === floor.id ? "red" : "gray", children: <div className={item.id === floor.id ? "context-message current" : "context-message"}><div><Space><Avatar size="small">{userName(item.authorId).slice(0, 1)}</Avatar><strong>{userName(item.authorId)}</strong></Space><small>{item.floorNumber ? `${item.floorNumber} 楼` : "待审"} · {dayjs(item.createdAt).format("HH:mm")}</small></div><p>{item.text}</p>{item.replyToId && <em>回复内容 ID：{item.replyToId}</em>}</div> }))} />
      </section>

      <section className="workspace-panel analysis-panel">
        <div className="workspace-panel-title"><span>02</span><div><strong>AI 初审与证据校验</strong><small>建议不是最终裁决</small></div></div>
        <div className="ai-summary"><RiskLevelTag level={floor.moderation.riskLevel} /><div><Progress percent={floor.moderation.riskScore} strokeColor={floor.moderation.riskLevel >= 3 ? "#c2413b" : "#c98322"} /><small>置信度 {Math.round(floor.moderation.confidence * 100)}%</small></div></div>
        <Space wrap>{floor.moderation.riskTypes.map((type) => <RiskTag key={type} type={type} />)}{floor.moderation.contextTags.map((type) => <RiskTag key={type} type={type} />)}</Space>
        <Descriptions column={1} size="small" className="review-descriptions">
          <Descriptions.Item label="说话者">{userName(floor.authorId)}</Descriptions.Item><Descriptions.Item label="涉及对象">{floor.moderation.targetUserIds.map(userName).join("、") || "未识别特定对象"}</Descriptions.Item><Descriptions.Item label="表达意图">{floor.moderation.intent}</Descriptions.Item><Descriptions.Item label="AI 建议">{floor.moderation.suggestedAction.toUpperCase()}</Descriptions.Item><Descriptions.Item label="系统分流">{floor.moderation.systemDecision.toUpperCase()}</Descriptions.Item>
        </Descriptions>
        <Typography.Title level={5}>证据真实性校验</Typography.Title>
        {floor.moderation.evidence.map((item) => <div className="review-evidence" key={item.quote}><div><CheckCircleOutlined /> 已定位 · {item.contentId}</div><blockquote>{item.quote}</blockquote><p>{item.reason}</p></div>)}
        <Alert type="warning" showIcon message="仍有不确定点" description={floor.moderation.uncertainties.join("；") || "暂无"} />
        {appeal && <div className="counter-analysis">
          <div className="counter-title"><RobotOutlined /><div><strong>申诉反证 AI</strong><small>主动挑战第一次判断，不直接给出终审结果</small></div></div>
          <div className="appeal-copy"><span>用户申诉</span><p>{appeal.reason}</p><small>补充上下文：{appeal.extraContext}</small></div>
          {appeal.counterAnalysis ? <><div className="argument-grid"><div className="argument-original"><strong><CloseCircleOutlined /> 支持维持原判</strong>{appeal.counterAnalysis.supportsOriginalDecision.map((item) => <p key={item}>{item}</p>)}</div><div className="argument-change"><strong><CheckCircleOutlined /> 支持改判</strong>{appeal.counterAnalysis.supportsChange.map((item) => <p key={item}>{item}</p>)}</div></div>
          <div className="counter-conclusion"><span>新证据影响</span><p>{appeal.counterAnalysis.newEvidenceImpact}</p><strong>{appeal.counterAnalysis.reviewSuggestion}</strong></div></> : <Alert type="info" showIcon message="申诉反证 Agent 暂未接入" description="当前仅保存用户申诉理由和补充上下文，由审核员直接进行人工判断。" />}
        </div>}
      </section>

      <section className="workspace-panel decision-panel">
        <div className="workspace-panel-title"><span>03</span><div><strong>人工最终裁决</strong><small>必须填写可追溯理由</small></div></div>
        {task.status === "resolved" ? <Alert type="success" showIcon message="该任务已完成" description={task.reviewReason} /> : <>
          <div className="human-boundary"><SafetyCertificateOutlined /><p><strong>人工责任边界</strong><br />请依据原文和上下文独立判断，不把 AI 分数当作结论。</p></div>
          <Form layout="vertical" initialValues={{ decision: defaultDecision }} onFinish={decide}>
            <Form.Item name="decision" label="最终处理结果" rules={[{ required: true }]}>
              <Radio.Group className="decision-card-group">
                <Radio value="allow"><strong>允许公开</strong><small>改判或确认安全，分配最新楼层</small></Radio>
                <Radio value="maintain_limit"><strong>维持限制</strong><small>证据充分，内容继续不公开</small></Radio>
                <Radio value="need_more_context"><strong>要求补充</strong><small>信息不足，暂不做强结论</small></Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="reason" label="具体复核理由" rules={[{ required: true, min: 10, message: "请至少填写 10 个字，说明使用了哪些上下文" }]}><Input.TextArea rows={7} maxLength={1000} showCount placeholder="例如：补充上下文证明攻击性片段属于引用，作者后半句明确表达反对，因此改判允许。" /></Form.Item>
            <Button type="primary" htmlType="submit" loading={saving} block>保存人工结论并写入时间线</Button>
          </Form>
        </>}
      </section>
    </div>
  </div>;
}
