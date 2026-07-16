import { FileSearchOutlined, ReloadOutlined } from "@ant-design/icons";
import { App, Button, Empty, List, Space, Spin, Typography } from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useState } from "react";
import { getMyAppeals } from "../api";
import { StatusTag } from "../components/StatusTag";
import type { Appeal } from "../types";

export function AppealsPage() {
  const { message } = App.useApp();
  const [items, setItems] = useState<Appeal[]>([]);
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true);
    try { setItems(await getMyAppeals()); }
    catch { message.error("申诉记录加载失败"); }
    finally { setLoading(false); }
  }, [message]);

  useEffect(() => { void load(); }, [load]);
  const statusAlias: Record<string, string> = {
    submitted: "appeal_submitted",
    reviewing: "pending_manual_review",
    approved: "appeal_approved",
    rejected: "appeal_rejected",
  };

  return (
    <div className="page narrow-page">
      <section className="page-heading">
        <div>
          <Typography.Title level={2}>我的申诉</Typography.Title>
          <Typography.Paragraph type="secondary">查看人工复核进度与最终处理结果。</Typography.Paragraph>
        </div>
        <Button icon={<ReloadOutlined />} onClick={() => void load()}>刷新</Button>
      </section>
      <Spin spinning={loading}>
        {items.length === 0 ? (
          <Empty image={<FileSearchOutlined className="large-empty-icon" />} description="暂无申诉记录" />
        ) : (
          <List
            dataSource={items}
            renderItem={(item) => (
              <List.Item className="appeal-card">
                <div className="appeal-card-header">
                  <Space wrap><StatusTag status={statusAlias[item.status] ?? item.status} /><Typography.Text code>{item.id.slice(0, 8)}</Typography.Text></Space>
                  <Typography.Text type="secondary">{dayjs(item.createdAt).format("YYYY-MM-DD HH:mm")}</Typography.Text>
                </div>
                <Typography.Paragraph strong ellipsis={{ rows: 2 }}>{item.contentText}</Typography.Paragraph>
                <div className="appeal-reason">
                  <Typography.Text type="secondary">申诉说明</Typography.Text>
                  <Typography.Paragraph>{item.reason}</Typography.Paragraph>
                </div>
              </List.Item>
            )}
          />
        )}
      </Spin>
    </div>
  );
}

