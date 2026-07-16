import { ArrowLeftOutlined, CheckCircleOutlined, EyeOutlined, MessageOutlined, RobotOutlined, SendOutlined } from "@ant-design/icons";
import { App, Avatar, Breadcrumb, Button, Divider, Empty, Input, Modal, Select, Space, Spin, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { RiskTag } from "../components/RiskTag";
import { StatusTag } from "../components/StatusTag";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";
import type { DemoFloor } from "../types";

const demoCases = [
  { label: "正常交流", value: "明天活动九点开始，大家记得提前二十分钟到。" },
  { label: "安全引用", value: "楼上说“你就是废物”这种话不合适，请不要这样攻击别人。" },
  { label: "连续骚扰", value: "大家都看看他平时是什么样。" },
  { label: "明确威胁", value: "你放学等着，我会让你后悔。" },
];

export function TopicDetailPage() {
  const { topicId = "" } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { user, users } = useAuth();
  const { findTopic, submitFloor } = useDemo();
  const topic = findTopic(topicId);
  const [text, setText] = useState("");
  const [replyToId, setReplyToId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<DemoFloor | null>(null);
  const userName = (id: string) => users.find((item) => item.id === id)?.displayName ?? "社区用户";

  const visibleFloors = useMemo(() => topic?.floors.filter((floor) => floor.visibleToPublic || floor.authorId === user.id) ?? [], [topic, user.id]);
  const publicFloors = topic?.floors.filter((floor) => floor.visibleToPublic) ?? [];
  const replyTarget = topic?.floors.find((floor) => floor.id === replyToId);

  if (!topic) return <div className="page"><Empty description="话题不存在"><Button onClick={() => navigate("/community")}>返回社区</Button></Empty></div>;

  const send = () => {
    if (!text.trim()) return;
    setSubmitting(true);
    window.setTimeout(() => {
      const created = submitFloor({ topicId: topic.id, text: text.trim(), replyToId, authorId: user.id });
      setText(""); setReplyToId(null); setResult(created); setSubmitting(false);
      message[created.visibleToPublic ? "success" : "warning"](created.moderation.userVisibleReason);
    }, 650);
  };

  return (
    <div className="page topic-detail-page">
      <Breadcrumb items={[{ title: <a onClick={() => navigate("/community")}>社区首页</a> }, { title: topic.category }, { title: topic.title }]} />
      <section className="topic-header-card">
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate("/community")}>返回话题列表</Button>
        <div className="topic-title-row"><div><Tag color="geekblue">{topic.category}</Tag><Typography.Title level={2}>{topic.title}</Typography.Title><Typography.Paragraph type="secondary">{topic.summary}</Typography.Paragraph></div><div className="topic-counter"><strong>{publicFloors.length}</strong><span>公开楼层</span></div></div>
        <Space split={<Divider type="vertical" />}><span>{userName(topic.authorId)} 发起</span><span>{dayjs(topic.createdAt).format("YYYY-MM-DD HH:mm")}</span><span><EyeOutlined /> {topic.viewCount} 次浏览</span></Space>
      </section>

      <section className="floor-list">
        {visibleFloors.map((floor) => {
          const reply = topic.floors.find((item) => item.id === floor.replyToId);
          const ownPrivate = !floor.visibleToPublic;
          return (
            <article className={`floor-card ${ownPrivate ? "floor-card-private" : ""}`} key={floor.id}>
              <div className="floor-rail"><span>{floor.floorNumber ? `${floor.floorNumber}F` : "待审"}</span></div>
              <div className="floor-content">
                <div className="floor-author"><Space><Avatar>{userName(floor.authorId).slice(0, 1)}</Avatar><div><strong>{userName(floor.authorId)}</strong><small>@{users.find((item) => item.id === floor.authorId)?.username}</small></div></Space><Space><StatusTag status={floor.status} /><Typography.Text type="secondary">{dayjs(floor.createdAt).format("MM-DD HH:mm")}</Typography.Text></Space></div>
                {reply && <div className="reply-context"><MessageOutlined /> 回复 {reply.floorNumber ?? "待审"} 楼 @{userName(reply.authorId)}：{reply.text.slice(0, 42)}</div>}
                <Typography.Paragraph className="floor-text">{floor.text}</Typography.Paragraph>
                {ownPrivate && <div className="private-content-note">仅你和审核员可见 · 审核通过前不会占用公开楼层号</div>}
                <div className="floor-actions"><Space>{floor.moderation.contextTags.slice(0, 2).map((tag) => <RiskTag key={tag} type={tag} />)}</Space>{floor.visibleToPublic && <Button type="text" size="small" icon={<MessageOutlined />} onClick={() => { setReplyToId(floor.id); document.getElementById("topic-composer")?.scrollIntoView({ behavior: "smooth" }); }}>回复该楼</Button>}</div>
              </div>
            </article>
          );
        })}
      </section>

      <section className="topic-composer" id="topic-composer">
        <div className="composer-heading"><div><Typography.Title level={4}>参与讨论</Typography.Title><Typography.Text type="secondary">以 {user.displayName} 身份发布，新内容先审核后公开</Typography.Text></div><Select placeholder="一键加载演示案例" options={demoCases} onChange={setText} value={undefined} className="demo-case-select" /></div>
        {replyTarget && <div className="active-reply"><span>正在回复 {replyTarget.floorNumber} 楼 @{userName(replyTarget.authorId)}</span><Button type="link" size="small" onClick={() => setReplyToId(null)}>取消回复</Button></div>}
        <Input.TextArea value={text} onChange={(event) => setText(event.target.value)} autoSize={{ minRows: 4, maxRows: 8 }} maxLength={2000} showCount placeholder="说清楚事实与观点，避免对他人进行人身评价" />
        <div className="composer-footer"><Space><RobotOutlined /><Typography.Text type="secondary">将读取当前话题、回复对象和最近 5 楼</Typography.Text></Space><Button type="primary" icon={<SendOutlined />} loading={submitting} disabled={!text.trim()} onClick={send}>提交审核</Button></div>
      </section>

      <Modal title="发布前审核结果" open={Boolean(result)} onCancel={() => setResult(null)} footer={null} width={640}>
        {result && <div className="moderation-result">
          <div className={`result-banner result-${result.moderation.systemDecision}`}><div>{result.visibleToPublic ? <CheckCircleOutlined /> : <RobotOutlined />}</div><div><StatusTag status={result.status} /><Typography.Title level={4}>{result.visibleToPublic ? `内容已公开为 ${result.floorNumber} 楼` : "内容暂未公开"}</Typography.Title><Typography.Paragraph>{result.moderation.userVisibleReason}</Typography.Paragraph></div></div>
          <div className="result-grid"><div><span>AI 建议</span><strong>{result.moderation.suggestedAction.toUpperCase()}</strong></div><div><span>系统分流</span><strong>{result.moderation.systemDecision.toUpperCase()}</strong></div><div><span>置信度</span><strong>{Math.round(result.moderation.confidence * 100)}%</strong></div></div>
          <Typography.Title level={5}>使用的上下文</Typography.Title><Space wrap>{result.moderation.contextUsed.map((item) => <Tag key={item}>{item}</Tag>)}</Space>
          {result.moderation.evidence.length > 0 && <><Typography.Title level={5} className="modal-section-title">可核验证据</Typography.Title>{result.moderation.evidence.map((item) => <div className="verified-evidence" key={item.quote}><span>“{item.quote}”</span><small><CheckCircleOutlined /> 已定位 · {item.reason}</small></div>)}</>}
          {!result.visibleToPublic && <Button type="primary" block className="modal-primary-action" onClick={() => navigate("/my-posts")}>前往“我的发布”查看并申诉</Button>}
        </div>}
      </Modal>
      {submitting && <Spin fullscreen tip="正在识别说话者、对象、意图与上下文…" />}
    </div>
  );
}
