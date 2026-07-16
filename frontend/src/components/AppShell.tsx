import {
  AuditOutlined,
  CommentOutlined,
  FileDoneOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SafetyCertificateOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Layout, Menu, Select, Space, Spin, Tooltip, Typography } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const { Header, Sider, Content } = Layout;

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, users, loading, selectUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const reviewer = user?.role === "reviewer" || user?.role === "admin";
  const menuItems = reviewer
    ? [{ key: "/reviewer", icon: <AuditOutlined />, label: "审核工作台" }]
    : [
        { key: "/community", icon: <CommentOutlined />, label: "社区讨论" },
        { key: "/appeals", icon: <FileDoneOutlined />, label: "我的申诉" },
      ];

  if (loading || !user) {
    return <Spin fullscreen tip="正在连接 ContextGuard" />;
  }

  const activeKey = location.pathname.startsWith("/reviewer") ? "/reviewer" : location.pathname;
  return (
    <Layout className="app-layout">
      <Sider width={224} collapsedWidth={72} collapsed={collapsed} className="app-sider" breakpoint="lg">
        <div className="brand">
          <div className="brand-mark"><SafetyCertificateOutlined /></div>
          {!collapsed && (
            <div>
              <Typography.Text className="brand-name">ContextGuard</Typography.Text>
              <Typography.Text className="brand-subtitle">上下文内容审核</Typography.Text>
            </div>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[activeKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="app-menu"
        />
        {!collapsed && <div className="environment-note">DEMO · Mock AI Provider</div>}
      </Sider>
      <Layout>
        <Header className="app-header">
          <div className="header-navigation">
            <Button
              type="text"
              className="desktop-sider-toggle"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed((value) => !value)}
              aria-label={collapsed ? "展开导航" : "收起导航"}
            />
            <div className="mobile-nav">
              {menuItems.map((item) => (
                <Tooltip title={item.label} key={item.key}>
                  <Button type={activeKey === item.key ? "primary" : "text"} icon={item.icon} onClick={() => navigate(item.key)} aria-label={String(item.label)} />
                </Tooltip>
              ))}
            </div>
          </div>
          <Space size={12} className="user-switcher">
            <div className="identity-copy">
              <Typography.Text type="secondary">模拟身份</Typography.Text>
              <Typography.Text strong>{user.role === "user" ? "普通用户" : "审核人员"}</Typography.Text>
            </div>
            <Select
              value={user.id}
              onChange={(value) => {
                selectUser(value);
                const next = users.find((item) => item.id === value);
                navigate(next?.role === "user" ? "/community" : "/reviewer");
                window.setTimeout(() => window.location.reload(), 0);
              }}
              options={users.map((item) => ({ label: `${item.displayName} · ${item.username}`, value: item.id }))}
              popupMatchSelectWidth={240}
              className="identity-select"
            />
            <Avatar>{user.displayName.slice(0, 1)}</Avatar>
          </Space>
        </Header>
        <Content className="app-content"><Outlet /></Content>
      </Layout>
    </Layout>
  );
}
