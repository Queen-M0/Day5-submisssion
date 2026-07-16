import { CheckCircleOutlined, ClockCircleOutlined, FileSearchOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Card, Empty, Space, Steps, Tag, Typography } from "antd";
import dayjs from "dayjs";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";
import { StatusTag } from "../components/StatusTag";

export function AppealsPage() {
  const { user } = useAuth();
  const { appeals, findFloor } = useDemo();
  const mine = appeals.filter((item) => item.authorId === user.id).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const statusAlias: Record<string, string> = { submitted: "appeal_submitted", reviewing: "appeal_reviewing", approved: "appeal_approved", rejected: "appeal_rejected", need_more_context: "need_more_context" };

  return <div className="page appeals-page">
    <section className="page-heading"><div><Typography.Title level={2}>我的申诉</Typography.Title><Typography.Paragraph type="secondary">查看补充上下文是否进入复核，以及审核员的最终处理结果。</Typography.Paragraph></div><div className="human-review-badge"><SafetyCertificateOutlined /> 人工最终裁决</div></section>
    {mine.length === 0 ? <Empty image={<FileSearchOutlined className="large-empty-icon" />} description="暂无申诉记录，请在“我的发布”中对受限内容发起申诉" /> : <div className="appeal-list">
      {mine.map((appeal) => {
        const found = findFloor(appeal.contentId);
        const final = ["approved", "rejected"].includes(appeal.status);
        const current = appeal.status === "submitted" ? 2 : appeal.status === "reviewing" ? 3 : final ? 4 : 3;
        return <Card key={appeal.id} className="appeal-detail-card">
          <div className="appeal-card-header"><Space><StatusTag status={statusAlias[appeal.status]} /><Tag color="blue">{appeal.appealType}</Tag></Space><Typography.Text type="secondary">{dayjs(appeal.createdAt).format("YYYY-MM-DD HH:mm")}</Typography.Text></div>
          <Typography.Text type="secondary">所属话题</Typography.Text><Typography.Title level={4}>{found?.topic.title}</Typography.Title>
          <div className="appealed-content">“{found?.floor.text}”</div>
          <div className="appeal-two-column"><div><span>申诉理由</span><p>{appeal.reason}</p></div><div><span>补充上下文</span><p>{appeal.extraContext}</p></div></div>
          <Steps current={current} size="small" items={[{ title: "原始限制" }, { title: "提交申诉" }, { title: "材料归档" }, { title: "人工复核" }, { title: "最终结果" }]} />
          {appeal.finalReason ? <div className={`final-decision final-${appeal.status}`}><CheckCircleOutlined /><div><strong>审核员最终理由</strong><p>{appeal.finalReason}</p></div></div> : <div className="waiting-review"><ClockCircleOutlined /><span>申诉材料已写入后端，当前等待审核员最终裁决。</span></div>}
        </Card>;
      })}
    </div>}
  </div>;
}
