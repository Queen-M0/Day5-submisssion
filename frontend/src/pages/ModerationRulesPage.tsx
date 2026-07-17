import { HistoryOutlined, SaveOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Alert, App, Button, Card, Checkbox, Col, Form, Input, InputNumber, Row, Skeleton, Slider, Space, Switch, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { getModerationRuleHistory, getModerationRules, updateModerationRules } from "../api";
import { apiErrorMessage } from "../api/client";
import type { ModerationRuleConfig } from "../types";

const riskOptions = [
  ["insult", "侮辱"], ["harassment", "骚扰"], ["threat", "威胁"],
  ["fraud", "欺诈"], ["discrimination", "歧视"], ["implicit_attack", "隐性攻击"],
].map(([value, label]) => ({ value, label }));

type RuleForm = Omit<ModerationRuleConfig, "id" | "version" | "isActive" | "updatedBy" | "createdAt">;

export function ModerationRulesPage() {
  const { message } = App.useApp();
  const [form] = Form.useForm<RuleForm>();
  const [current, setCurrent] = useState<ModerationRuleConfig | null>(null);
  const [history, setHistory] = useState<ModerationRuleConfig[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const [rule, versions] = await Promise.all([getModerationRules(), getModerationRuleHistory()]);
      setCurrent(rule); setHistory(versions);
      form.setFieldsValue({
        name: rule.name,
        enabledRiskTypes: rule.enabledRiskTypes,
        autoLimitMinRiskLevel: rule.autoLimitMinRiskLevel,
        manualReviewMinRiskLevel: rule.manualReviewMinRiskLevel,
        minConfidence: rule.minConfidence,
        requireGroundedEvidence: rule.requireGroundedEvidence,
        routeDivergenceToManual: rule.routeDivergenceToManual,
        changeReason: "",
      });
    } catch (caught) { setError(apiErrorMessage(caught)); }
  };
  useEffect(() => { void load(); }, []);

  const save = async (values: RuleForm) => {
    setSaving(true);
    try {
      const next = await updateModerationRules(values);
      message.success(`规则已发布为 ${next.version}，后续新内容立即使用`);
      await load();
    } catch (caught) { message.error(apiErrorMessage(caught)); } finally { setSaving(false); }
  };

  if (!current && !error) return <div className="page"><Skeleton active /></div>;
  if (!current) return <div className="page"><Alert type="error" showIcon message="规则配置加载失败" description={error} /></div>;
  return <div className="page moderation-rules-page">
    <section className="page-heading"><div><Typography.Title level={2}>审核规则配置</Typography.Title><Typography.Paragraph type="secondary">配置系统分流边界。保存时生成新版本，旧版本不会被覆盖，历史审核记录仍保留当时使用的版本。</Typography.Paragraph></div><Tag color="green" icon={<SafetyCertificateOutlined />}>当前生效 {current.version}</Tag></section>
    <Alert type="info" showIcon message="规则只控制自动分流，不改变 AI 原始输出" description="证据不可信、置信度不足或双模型分歧时优先转人工；人工审核员仍拥有最终裁决权。" />
    <Card className="rule-editor-card" title="发布新规则版本">
      <Form form={form} layout="vertical" onFinish={save}>
        <Row gutter={24}>
          <Col xs={24} lg={12}><Form.Item name="name" label="规则名称" rules={[{ required: true, min: 2 }]}><Input /></Form.Item></Col>
          <Col xs={24} lg={12}><Form.Item name="minConfidence" label="自动处置最低置信度" rules={[{ required: true }]}><Slider min={0} max={1} step={0.05} marks={{ 0: "0", 0.65: "0.65", 1: "1" }} /></Form.Item></Col>
          <Col span={24}><Form.Item name="enabledRiskTypes" label="允许规则自动处置的风险类型" rules={[{ required: true }]}><Checkbox.Group options={riskOptions} /></Form.Item></Col>
          <Col xs={24} md={12}><Form.Item name="manualReviewMinRiskLevel" label="转人工最低风险等级" rules={[{ required: true }]}><InputNumber min={1} max={3} addonBefore="L" style={{ width: "100%" }} /></Form.Item></Col>
          <Col xs={24} md={12}><Form.Item name="autoLimitMinRiskLevel" label="自动限制最低风险等级" rules={[{ required: true }]}><InputNumber min={1} max={3} addonBefore="L" style={{ width: "100%" }} /></Form.Item></Col>
          <Col xs={24} md={12}><Form.Item name="requireGroundedEvidence" label="限制性决定必须有可定位证据" valuePropName="checked"><Switch checkedChildren="必须" unCheckedChildren="关闭" /></Form.Item></Col>
          <Col xs={24} md={12}><Form.Item name="routeDivergenceToManual" label="双模型分歧自动转人工" valuePropName="checked"><Switch checkedChildren="转人工" unCheckedChildren="按主模型" /></Form.Item></Col>
          <Col span={24}><Form.Item name="changeReason" label="修改理由" rules={[{ required: true, min: 5, message: "请至少填写 5 个字，便于审计追溯" }]}><Input.TextArea rows={3} maxLength={500} showCount placeholder="例如：比赛演示期提高低置信度案例的人工复核比例" /></Form.Item></Col>
        </Row>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>保存并发布新版本</Button>
      </Form>
    </Card>
    <Card title={<Space><HistoryOutlined />规则版本历史</Space>}>
      <Table rowKey="id" pagination={false} dataSource={history} columns={[
        { title: "版本", dataIndex: "version", render: (value, row) => <Space><strong>{value}</strong>{row.isActive && <Tag color="green">生效中</Tag>}</Space> },
        { title: "阈值", render: (_, row) => `人工 L${row.manualReviewMinRiskLevel} / 限制 L${row.autoLimitMinRiskLevel} / 置信度 ${row.minConfidence}` },
        { title: "修改理由", dataIndex: "changeReason" },
        { title: "更新时间", dataIndex: "createdAt", render: (value) => dayjs(value).format("YYYY-MM-DD HH:mm") },
      ]} />
    </Card>
  </div>;
}
