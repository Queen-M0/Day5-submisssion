import {
  ArrowRightOutlined,
  EyeOutlined,
  MessageOutlined,
  ReloadOutlined,
  SendOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App,
  Button,
  Empty,
  Form,
  Input,
  List,
  Modal,
  Select,
  Space,
  Spin,
  Typography,
} from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useMemo, useState } from "react";
import { createContent, getContents, getScenes, submitAppeal } from "../api";
import { RiskTag } from "../components/RiskTag";
import { StatusTag } from "../components/StatusTag";
import { useAuth } from "../context/AuthContext";
import type { ContentItem, Scene } from "../types";

const demoCases = [
  { label: "正常交流", value: "这次小组作业我们今晚八点开会讨论吧。" },
  { label: "明确辱骂", value: "你就是废物，别来拖累我们。" },
  { label: "安全引用", value: "楼上说“你就是废物”这种话不合适，请管理员处理。" },
  { label: "隐晦攻击", value: "别让那个“大聪明”碰展示，懂的都懂。" },
  { label: "明确威胁", value: "你放学等着，我会让你后悔。" },
];

export function CommunityPage() {
  const { message } = App.useApp();
  const { user } = useAuth();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [text, setText] = useState("");
  const [parentId, setParentId] = useState<string | null>(null);
  const [selected, setSelected] = useState<ContentItem | null>(null);
  const [appealTarget, setAppealTarget] = useState<ContentItem | null>(null);
  const [appealForm] = Form.useForm();
  const scene = scenes[0];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const loadedScenes = await getScenes();
      setScenes(loadedScenes);
      if (loadedScenes[0]) setContents(await getContents(loadedScenes[0].id));
    } catch {
      message.error("无法加载社区数据，请确认后端已启动并完成 seed");
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => { void load(); }, [load, user?.id]);

  const replyOptions = useMemo(
    () => contents.filter((item) => item.visibleToPublic).map((item, index) => ({
      value: item.id,
      label: `${index + 1} 楼 · ${item.author.displayName}：${item.text.slice(0, 24)}`,
    })),
    [contents],
  );

  const send = async () => {
    if (!text.trim() || !scene) return;
    setSubmitting(true);
    try {
      const result = await createContent({ sceneId: scene.id, contentType: "forum_reply", parentId, text });
      setText("");
      setParentId(null);
      message[result.decision === "publish" ? "success" : "warning"](result.userVisibleReason);
      await load();
    } catch {
      message.error("发布失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  };

  const appeal = async (values: { appealType: string; reason: string }) => {
    if (!appealTarget) return;
    await submitAppeal(appealTarget.id, values);
    message.success("申诉已提交，审核员会结合上下文进行人工复核");
    setAppealTarget(null);
    appealForm.resetFields();
    await load();
  };

  return (
    <div className="page community-page">
      <section className="page-heading">
        <div>
          <Typography.Title level={2}>{scene?.title ?? "校园交流社区"}</Typography.Title>
          <Typography.Paragraph type="secondary">{scene?.description}</Typography.Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => void load()}>刷新</Button>
      </section>

      <section className="composer-panel">
        <div className="composer-topline">
          <Typography.Text strong>发布新楼层</Typography.Text>
          <Select
            placeholder="载入演示样例"
            options={demoCases}
            onChange={setText}
            value={undefined}
            className="demo-case-select"
          />
        </div>
        <Input.TextArea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="输入你想参与讨论的内容"
          autoSize={{ minRows: 3, maxRows: 7 }}
          maxLength={2000}
          showCount
        />
        <div className="composer-actions">
          <Select
            allowClear
            showSearch
            placeholder="引用某一楼（可选）"
            value={parentId}
            onChange={(value) => setParentId(value ?? null)}
            options={replyOptions}
            className="reply-select"
          />
          <Button type="primary" icon={<SendOutlined />} loading={submitting} disabled={!text.trim()} onClick={() => void send()}>
            提交审核
          </Button>
        </div>
      </section>

      <Alert
        type="info"
        showIcon
        message="当前使用确定性的 Mock AI Provider，适合稳定演示；真实模型将在后续 Agent 分支接入。"
        className="demo-alert"
      />

      <section className="discussion-section">
        <div className="section-title-row">
          <Typography.Title level={4}>讨论楼层</Typography.Title>
          <Typography.Text type="secondary">共 {contents.length} 条</Typography.Text>
        </div>
        <Spin spinning={loading}>
          {contents.length === 0 ? <Empty description="还没有讨论内容" /> : (
            <List
              dataSource={contents}
              renderItem={(item, index) => {
                const own = item.author.id === user?.id;
                return (
                  <List.Item className={`message-card ${!item.visibleToPublic ? "message-card-limited" : ""}`}>
                    <div className="floor-index">{index + 1}F</div>
                    <div className="message-body">
                      <div className="message-meta">
                        <Space wrap>
                          <Typography.Text strong>{item.author.displayName}</Typography.Text>
                          <Typography.Text type="secondary">@{item.author.username}</Typography.Text>
                          {item.parentAuthorName && <Typography.Text type="secondary">回复 {item.parentAuthorName}</Typography.Text>}
                        </Space>
                        <Typography.Text type="secondary">{dayjs(item.createdAt).format("MM-DD HH:mm")}</Typography.Text>
                      </div>
                      <Typography.Paragraph className="message-text">{item.text}</Typography.Paragraph>
                      <div className="message-footer">
                        <Space wrap>
                          <StatusTag status={item.status} />
                          {item.moderation?.riskTypes.map((type) => <RiskTag key={type} type={type} />)}
                        </Space>
                        <Space>
                          {own && item.moderation && (
                            <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => setSelected(item)}>查看结果</Button>
                          )}
                          {own && ["limited", "pending_manual_review"].includes(item.status) && (
                            <Button size="small" type="link" icon={<MessageOutlined />} onClick={() => setAppealTarget(item)}>申诉</Button>
                          )}
                        </Space>
                      </div>
                    </div>
                  </List.Item>
                );
              }}
            />
          )}
        </Spin>
      </section>

      <Modal title="审核结果" open={Boolean(selected)} onCancel={() => setSelected(null)} footer={null}>
        {selected?.moderation && (
          <Space direction="vertical" size={16} className="modal-stack">
            <div><StatusTag status={selected.status} /></div>
            <Typography.Paragraph>{selected.moderation.userVisibleReason}</Typography.Paragraph>
            <div>
              <Typography.Text type="secondary">风险类型</Typography.Text>
              <div className="tag-row">
                {selected.moderation.riskTypes.length
                  ? selected.moderation.riskTypes.map((type) => <RiskTag key={type} type={type} />)
                  : <Typography.Text>未发现明确风险</Typography.Text>}
              </div>
            </div>
            {["limited", "pending_manual_review"].includes(selected.status) && (
              <Button type="primary" onClick={() => { setAppealTarget(selected); setSelected(null); }}>
                提交申诉 <ArrowRightOutlined />
              </Button>
            )}
          </Space>
        )}
      </Modal>

      <Modal title="提交申诉" open={Boolean(appealTarget)} onCancel={() => setAppealTarget(null)} footer={null} destroyOnClose>
        <Typography.Paragraph type="secondary">审核员将查看原始内容、上下文和你的补充说明，申诉不会交给同一个 AI 自动裁决。</Typography.Paragraph>
        <Form form={appealForm} layout="vertical" onFinish={(values) => void appeal(values)}>
          <Form.Item label="申诉类型" name="appealType" initialValue="quote_or_report" rules={[{ required: true }]}>
            <Select options={[
              { value: "quote_or_report", label: "我是在引用、反驳或举报" },
              { value: "joke_or_misunderstanding", label: "这是玩笑或误会" },
              { value: "missing_context", label: "内容被断章取义" },
              { value: "other", label: "其他" },
            ]} />
          </Form.Item>
          <Form.Item label="补充说明" name="reason" rules={[{ required: true, min: 5, message: "请至少填写 5 个字" }]}>
            <Input.TextArea rows={4} maxLength={1000} showCount placeholder="说明引用关系、真实语境或缺失的上下文" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>提交给审核员</Button>
        </Form>
      </Modal>
    </div>
  );
}
