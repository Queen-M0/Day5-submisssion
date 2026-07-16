import {
  ArrowRightOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CommentOutlined,
  EyeOutlined,
  FileProtectOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { App, Button, Card, Col, Form, Input, Modal, Row, Select, Space, Statistic, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";

const categories = ["全部话题", "训练营协作", "校园活动", "失物招领"];

export function CommunityPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { user, users } = useAuth();
  const { topics, reviewTasks, createTopic } = useDemo();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("全部话题");
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const publicTopics = useMemo(() => topics.filter((topic) => topic.floors.some((floor) => floor.floorNumber === 1 && floor.visibleToPublic)), [topics]);
  const filtered = publicTopics.filter((topic) => (category === "全部话题" || topic.category === category) && `${topic.title}${topic.summary}`.includes(query.trim()));
  const publicFloors = publicTopics.flatMap((topic) => topic.floors).filter((floor) => floor.visibleToPublic).length;
  const pending = reviewTasks.filter((task) => task.status === "pending").length;
  const userName = (id: string) => users.find((item) => item.id === id)?.displayName ?? "社区用户";

  const submitTopic = (values: { title: string; body: string; category: string }) => {
    const topicId = createTopic({ ...values, authorId: user.id });
    setOpen(false);
    form.resetFields();
    message.success("AI 审核通过，话题已公开并分配 1 楼");
    navigate(`/topics/${topicId}`);
  };

  return (
    <div className="page community-home-page">
      <section className="community-hero">
        <div className="hero-copy">
          <Space className="eyebrow"><SafetyCertificateOutlined /><span>固定社区 · 发布前上下文审核</span></Space>
          <Typography.Title level={1}>AI Native 青年讨论社区</Typography.Title>
          <Typography.Paragraph>在同一个社区中围绕多个话题交流。每一楼公开前都会分析说话者、对象、意图与上下文；有争议时由审核员接管。</Typography.Paragraph>
          <Space wrap>
            <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setOpen(true)}>发起新话题</Button>
            <Button size="large" onClick={() => navigate("/my-posts")}>查看我的发布</Button>
          </Space>
        </div>
        <div className="hero-proof-card">
          <div className="proof-label">本原型要证明</div>
          <div className="proof-item"><CheckCircleOutlined /><span>安全引用不会被敏感词误杀</span></div>
          <div className="proof-item"><CheckCircleOutlined /><span>隐晦骚扰会结合连续对话识别</span></div>
          <div className="proof-item"><CheckCircleOutlined /><span>AI 错误可申诉、可人工改判</span></div>
          <div className="proof-foot">AI 给建议，系统做分流，人工做终审</div>
        </div>
      </section>

      <section className="community-stats">
        <Statistic title="公开话题" value={publicTopics.length} prefix={<CommentOutlined />} />
        <Statistic title="公开楼层" value={publicFloors} prefix={<FileProtectOutlined />} />
        <Statistic title="社区成员" value={3} prefix={<TeamOutlined />} />
        <Statistic title="待人工复核" value={pending} prefix={<ClockCircleOutlined />} />
      </section>

      <div className="community-layout">
        <main>
          <div className="section-heading">
            <div><Typography.Title level={3}>社区话题</Typography.Title><Typography.Text type="secondary">线性楼层展示，回复指定楼层但不产生嵌套评论</Typography.Text></div>
            <Input allowClear prefix={<SearchOutlined />} placeholder="搜索话题" value={query} onChange={(event) => setQuery(event.target.value)} className="topic-search" />
          </div>
          <div className="category-tabs">
            {categories.map((item) => <Button key={item} type={category === item ? "primary" : "text"} onClick={() => setCategory(item)}>{item}</Button>)}
          </div>
          <div className="topic-list">
            {filtered.map((topic) => {
              const floors = topic.floors.filter((floor) => floor.visibleToPublic);
              const last = floors[floors.length - 1];
              return (
                <Card key={topic.id} className="topic-card" hoverable onClick={() => navigate(`/topics/${topic.id}`)}>
                  <div className="topic-card-top"><Tag color="geekblue">{topic.category}</Tag><Typography.Text type="secondary">更新于 {dayjs(topic.lastActiveAt).format("MM-DD HH:mm")}</Typography.Text></div>
                  <Typography.Title level={4}>{topic.title}</Typography.Title>
                  <Typography.Paragraph type="secondary" ellipsis={{ rows: 2 }}>{topic.summary}</Typography.Paragraph>
                  <div className="topic-card-bottom">
                    <Space split={<span className="meta-divider" />}>
                      <span>{userName(topic.authorId)} 发起</span><span>{floors.length} 楼</span><span><EyeOutlined /> {topic.viewCount}</span>
                    </Space>
                    <Space><Typography.Text type="secondary">最新：{last ? userName(last.authorId) : "—"}</Typography.Text><ArrowRightOutlined /></Space>
                  </div>
                </Card>
              );
            })}
          </div>
        </main>
        <aside className="community-aside">
          <Card className="aside-card" title="发布审核闭环">
            <div className="flow-step"><span>01</span><div><strong>提交内容</strong><small>暂不公开，不提前占楼</small></div></div>
            <div className="flow-step"><span>02</span><div><strong>AI 分析上下文</strong><small>说话者 · 对象 · 意图 · 引用</small></div></div>
            <div className="flow-step"><span>03</span><div><strong>系统分流</strong><small>允许 · 限制 · 人工复核</small></div></div>
            <div className="flow-step"><span>04</span><div><strong>申诉与改判</strong><small>补充上下文，审核员最终裁决</small></div></div>
          </Card>
          <Card className="aside-card demo-guide" title="推荐演示路径">
            <ol><li>进入“团队赛展示”话题</li><li>加载隐晦骚扰样例并提交</li><li>切换张三查看申诉</li><li>切换审核员完成改判</li></ol>
          </Card>
        </aside>
      </div>

      <Modal title="发起新话题" open={open} onCancel={() => setOpen(false)} footer={null} width={620} destroyOnClose>
        <div className="modal-intro"><SafetyCertificateOutlined /><span>1 楼审核通过后，话题才会出现在公开社区。</span></div>
        <Form form={form} layout="vertical" onFinish={submitTopic} initialValues={{ category: "训练营协作" }}>
          <Form.Item label="话题标题" name="title" rules={[{ required: true, min: 4, message: "请填写至少 4 个字" }]}><Input maxLength={60} showCount placeholder="用一句话说明要讨论什么" /></Form.Item>
          <Form.Item label="话题分类" name="category" rules={[{ required: true }]}><Select options={categories.slice(1).map((item) => ({ label: item, value: item }))} /></Form.Item>
          <Form.Item label="1 楼正文" name="body" rules={[{ required: true, min: 5 }]}><Input.TextArea rows={6} maxLength={2000} showCount placeholder="输入话题正文，提交后将进行上下文审核" /></Form.Item>
          <Button type="primary" htmlType="submit" block>提交 AI 审核并发布</Button>
        </Form>
      </Modal>
    </div>
  );
}
