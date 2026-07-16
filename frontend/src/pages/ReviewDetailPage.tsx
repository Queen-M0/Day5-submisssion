import { ArrowLeftOutlined, CheckOutlined } from "@ant-design/icons";
import {
  Alert,
  App,
  Button,
  Descriptions,
  Form,
  Input,
  Progress,
  Radio,
  Select,
  Space,
  Spin,
  Timeline,
  Typography,
} from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getReviewTask, submitReview } from "../api";
import { RiskLevelTag, RiskTag } from "../components/RiskTag";
import type { ReviewTaskDetail } from "../types";

export function ReviewDetailPage() {
  const { message } = App.useApp();
  const { taskId = "" } = useParams();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ReviewTaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    getReviewTask(taskId)
      .then(setDetail)
      .catch(() => message.error("复核任务不存在或已被处理"))
      .finally(() => setLoading(false));
  }, [message, taskId]);

  const decide = async (values: {
    finalDecision: string;
    finalRiskLevel: number;
    correctionType: string;
    reviewReason: string;
  }) => {
    setSaving(true);
    try {
      await submitReview(taskId, values);
      message.success("人工复核结论已保存");
      navigate("/reviewer");
    } catch {
      message.error("保存失败，该任务可能已经处理");
    } finally { setSaving(false); }
  };

  if (loading) return <Spin fullscreen tip="正在加载完整上下文" />;
  if (!detail) return null;
  const { moderation, content, appeal } = detail;

  return (
    <div className="review-detail-page">
      <div className="review-detail-header">
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/reviewer")}>返回队列</Button>
        <div>
          <Typography.Title level={3}>人工复核</Typography.Title>
          <Typography.Text type="secondary">任务 {taskId.slice(0, 20)}</Typography.Text>
        </div>
      </div>
      <div className="review-grid">
        <section className="review-column context-column">
          <div className="column-heading">
            <Typography.Title level={5}>上下文时间线</Typography.Title>
            <Typography.Text type="secondary">最近 {detail.context.length} 条</Typography.Text>
          </div>
          <Timeline
            items={detail.context.map((item) => ({
              color: item.id === content.id ? "red" : "gray",
              children: (
                <div className={item.id === content.id ? "timeline-current" : "timeline-message"}>
                  <div className="timeline-meta">
                    <Typography.Text strong>{item.author.displayName}</Typography.Text>
                    <Typography.Text type="secondary">{dayjs(item.createdAt).format("HH:mm")}</Typography.Text>
                  </div>
                  <Typography.Paragraph>{item.text}</Typography.Paragraph>
                </div>
              ),
            }))}
          />
        </section>

        <section className="review-column analysis-column">
          <div className="column-heading"><Typography.Title level={5}>AI 初审分析</Typography.Title></div>
          <div className="risk-overview">
            <RiskLevelTag level={moderation.riskLevel} />
            <Progress
              percent={moderation.riskScore}
              size="small"
              strokeColor={moderation.riskLevel >= 3 ? "#c23b32" : "#d97706"}
              format={(value) => `${value} 分`}
            />
          </div>
          <Space wrap className="tag-row">
            {moderation.riskTypes.map((type) => <RiskTag key={type} type={type} />)}
          </Space>
          <Descriptions column={1} size="small" className="analysis-descriptions">
            <Descriptions.Item label="AI 建议">{moderation.decision}</Descriptions.Item>
            <Descriptions.Item label="置信度">{Math.round(moderation.confidence * 100)}%</Descriptions.Item>
            <Descriptions.Item label="上下文判断">{moderation.contextReasoning}</Descriptions.Item>
          </Descriptions>
          <div className="evidence-list">
            <Typography.Text strong>证据片段</Typography.Text>
            {moderation.evidence?.length ? moderation.evidence.map((item, index) => (
              <div className="evidence-item" key={`${item.text}-${index}`}>
                <Typography.Text mark>{item.text}</Typography.Text>
                <Typography.Paragraph type="secondary">{item.reason}</Typography.Paragraph>
              </div>
            )) : <Typography.Paragraph type="secondary">未提取到明确风险证据</Typography.Paragraph>}
          </div>
          <Alert type="warning" showIcon message="审核员提示" description={moderation.reviewerReason} />
          {appeal && (
            <div className="appeal-panel">
              <Typography.Text strong>用户申诉</Typography.Text>
              <Typography.Paragraph>{appeal.reason}</Typography.Paragraph>
              <Typography.Text type="secondary">类型：{appeal.appealType}</Typography.Text>
            </div>
          )}
        </section>

        <section className="review-column decision-column">
          <div className="column-heading"><Typography.Title level={5}>人工结论</Typography.Title></div>
          <Form
            form={form}
            layout="vertical"
            initialValues={{ finalDecision: "publish", finalRiskLevel: moderation.riskLevel, correctionType: "false_positive_context" }}
            onFinish={(values) => void decide(values)}
          >
            <Form.Item name="finalDecision" label="处理结果" rules={[{ required: true }]}>
              <Radio.Group className="decision-radio">
                <Radio.Button value="publish">改为发布</Radio.Button>
                <Radio.Button value="maintain_limit">维持限制</Radio.Button>
                <Radio.Button value="require_edit">要求修改</Radio.Button>
                <Radio.Button value="escalate">升级风险</Radio.Button>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="finalRiskLevel" label="最终风险等级" rules={[{ required: true }]}>
              <Select options={[
                { value: 0, label: "L0 安全" },
                { value: 1, label: "L1 低风险" },
                { value: 2, label: "L2 中风险" },
                { value: 3, label: "L3 高风险" },
              ]} />
            </Form.Item>
            <Form.Item name="correctionType" label="校正类型" rules={[{ required: true }]}>
              <Select options={[
                { value: "correct", label: "AI 判断正确" },
                { value: "false_positive_quote", label: "引用语境误判" },
                { value: "false_positive_context", label: "上下文误判" },
                { value: "false_positive_joke", label: "玩笑误判" },
                { value: "false_negative_implicit", label: "隐晦攻击漏判" },
                { value: "policy_unclear", label: "规则不明确" },
              ]} />
            </Form.Item>
            <Form.Item name="reviewReason" label="复核理由" rules={[{ required: true, min: 5, message: "请填写可追溯的复核理由" }]}>
              <Input.TextArea rows={7} maxLength={1000} showCount placeholder="说明采用了哪些上下文证据，以及维持或改判的原因" />
            </Form.Item>
            <Button type="primary" htmlType="submit" icon={<CheckOutlined />} loading={saving} block>保存最终结论</Button>
          </Form>
        </section>
      </div>
    </div>
  );
}
