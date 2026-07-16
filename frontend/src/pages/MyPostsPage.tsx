import { CheckCircleOutlined, EyeOutlined, FileSearchOutlined, MessageOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { App, Button, Card, Descriptions, Drawer, Empty, Form, Input, Modal, Select, Space, Tabs, Tag, Timeline, Typography } from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RiskTag } from "../components/RiskTag";
import { StatusTag } from "../components/StatusTag";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";
import type { DemoFloor, DemoTopic } from "../types";

type OwnedItem = { topic: DemoTopic; floor: DemoFloor };

export function MyPostsPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { topics, submitAppeal, findAppeal } = useDemo();
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<OwnedItem | null>(null);
  const [appealTarget, setAppealTarget] = useState<OwnedItem | null>(null);
  const [form] = Form.useForm();

  const owned = useMemo(() => topics.flatMap((topic) => topic.floors.filter((floor) => floor.authorId === user.id).map((floor) => ({ topic, floor }))).sort((a, b) => b.floor.createdAt.localeCompare(a.floor.createdAt)), [topics, user.id]);
  const categories: Record<string, string[]> = {
    pending: ["pending_manual_review", "need_more_context"],
    limited: ["limited", "appeal_rejected"],
    appeal: ["appeal_submitted", "appeal_reviewing", "appeal_approved"],
  };
  const visible = filter === "all" ? owned : owned.filter((item) => categories[filter]?.includes(item.floor.status));

  const appeal = (values: { appealType: string; reason: string; extraContext: string }) => {
    if (!appealTarget) return;
    submitAppeal({ contentId: appealTarget.floor.id, authorId: user.id, ...values });
    form.resetFields(); setAppealTarget(null); message.success("申诉已提交：AI 将提供反证，最终由审核员裁决");
  };

  return (
    <div className="page my-posts-page">
      <section className="page-heading"><div><Typography.Title level={2}>我的发布</Typography.Title><Typography.Paragraph type="secondary">审核中、受限和申诉内容只对你和审核员可见，不会造成公开楼层空号。</Typography.Paragraph></div><div className="privacy-badge"><SafetyCertificateOutlined /> 权限隔离已生效</div></section>
      <Tabs activeKey={filter} onChange={setFilter} items={[
        { key: "all", label: `全部 ${owned.length}` },
        { key: "pending", label: `待复核 ${owned.filter((item) => categories.pending.includes(item.floor.status)).length}` },
        { key: "limited", label: `已限制 ${owned.filter((item) => categories.limited.includes(item.floor.status)).length}` },
        { key: "appeal", label: `申诉中/完成 ${owned.filter((item) => categories.appeal.includes(item.floor.status)).length}` },
      ]} />
      {visible.length === 0 ? <Empty image={<FileSearchOutlined className="large-empty-icon" />} description="当前筛选下没有发布记录" /> : <div className="owned-content-list">
        {visible.map((item) => {
          const appealRecord = findAppeal(item.floor.id);
          const appealable = ["limited", "pending_manual_review", "need_more_context"].includes(item.floor.status) && !appealRecord;
          return <Card key={item.floor.id} className="owned-content-card">
            <div className="owned-card-head"><Space wrap><StatusTag status={item.floor.status} /><Tag>{item.topic.category}</Tag><Typography.Text type="secondary">{item.floor.floorNumber ? `${item.floor.floorNumber} 楼` : "未占公开楼层"}</Typography.Text></Space><Typography.Text type="secondary">{dayjs(item.floor.createdAt).format("MM-DD HH:mm")}</Typography.Text></div>
            <Typography.Text className="owned-topic" onClick={() => navigate(`/topics/${item.topic.id}`)}>{item.topic.title}</Typography.Text>
            <Typography.Paragraph className="owned-text" ellipsis={{ rows: 2 }}>{item.floor.text}</Typography.Paragraph>
            <div className="reason-strip"><span>系统说明</span><p>{item.floor.moderation.userVisibleReason}</p></div>
            <div className="owned-card-actions"><Space wrap>{item.floor.moderation.riskTypes.map((type) => <RiskTag key={type} type={type} />)}</Space><Space><Button icon={<EyeOutlined />} onClick={() => setSelected(item)}>审核详情</Button>{appealable && <Button type="primary" icon={<MessageOutlined />} onClick={() => setAppealTarget(item)}>发起申诉</Button>}</Space></div>
          </Card>;
        })}
      </div>}

      <Drawer title="审核详情与时间线" width={600} open={Boolean(selected)} onClose={() => setSelected(null)}>
        {selected && <div className="audit-drawer">
          <StatusTag status={selected.floor.status} /><Typography.Title level={4}>{selected.floor.text}</Typography.Title>
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="风险等级">L{selected.floor.moderation.riskLevel} · {selected.floor.moderation.riskScore} 分</Descriptions.Item>
            <Descriptions.Item label="表达意图">{selected.floor.moderation.intent}</Descriptions.Item>
            <Descriptions.Item label="AI 建议">{selected.floor.moderation.suggestedAction}</Descriptions.Item>
            <Descriptions.Item label="系统分流">{selected.floor.moderation.systemDecision}</Descriptions.Item>
          </Descriptions>
          <Typography.Title level={5}>上下文与不确定点</Typography.Title><Space wrap>{selected.floor.moderation.contextUsed.map((item) => <Tag key={item}>{item}</Tag>)}</Space>
          {selected.floor.moderation.uncertainties.map((item) => <div className="uncertainty-item" key={item}>{item}</div>)}
          <Typography.Title level={5}>证据校验</Typography.Title>
          {selected.floor.moderation.evidence.length ? selected.floor.moderation.evidence.map((item) => <div className="verified-evidence" key={item.quote}><span>“{item.quote}”</span><small><CheckCircleOutlined /> 已定位到 {item.contentId} · {item.reason}</small></div>) : <Typography.Paragraph type="secondary">未发现需要限制的风险证据。</Typography.Paragraph>}
          <Typography.Title level={5}>处理时间线</Typography.Title><Timeline items={selected.floor.auditTrail.map((event) => ({ color: event.tone === "success" ? "green" : event.tone === "danger" ? "red" : event.tone === "warning" ? "orange" : "blue", children: <div><strong>{event.title}</strong><p>{event.description}</p><small>{event.actor} · {dayjs(event.time).format("MM-DD HH:mm:ss")}</small></div> }))} />
        </div>}
      </Drawer>

      <Modal title="提交内容申诉" open={Boolean(appealTarget)} onCancel={() => setAppealTarget(null)} footer={null} width={600} destroyOnClose>
        {appealTarget && <><div className="appeal-target-copy"><span>原内容</span><p>{appealTarget.floor.text}</p></div><Typography.Paragraph type="secondary">申诉不会把相同输入交给 AI 自动终审。系统会读取补充上下文，生成支持维持与支持改判的两组依据，再由审核员决定。</Typography.Paragraph></>}
        <Form form={form} layout="vertical" onFinish={appeal} initialValues={{ appealType: "quote_or_report" }}>
          <Form.Item label="申诉类型" name="appealType" rules={[{ required: true }]}><Select options={[{ value: "quote_or_report", label: "引用、反驳或举报被误判" }, { value: "missing_context", label: "缺少关键上下文" }, { value: "joke_or_misunderstanding", label: "玩笑或关系被误解" }, { value: "other", label: "其他" }]} /></Form.Item>
          <Form.Item label="申诉理由" name="reason" rules={[{ required: true, min: 8, message: "请具体说明至少 8 个字" }]}><Input.TextArea rows={3} maxLength={600} showCount placeholder="说明第一次判断可能错在哪里" /></Form.Item>
          <Form.Item label="补充上下文" name="extraContext" rules={[{ required: true, min: 8, message: "请补充能帮助复核的上下文" }]}><Input.TextArea rows={4} maxLength={1000} showCount placeholder="例如引用来自哪一楼、真实对话关系或被遗漏的前文" /></Form.Item>
          <Button type="primary" htmlType="submit" block>提交申诉并进入人工复核</Button>
        </Form>
      </Modal>
    </div>
  );
}
