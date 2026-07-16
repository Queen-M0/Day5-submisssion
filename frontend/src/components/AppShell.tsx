import {
  AuditOutlined,
  CommentOutlined,
  FileDoneOutlined,
  HistoryOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Layout, Menu, Select, Space, Tag, Tooltip, Typography } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";

const { Header, Sider, Content } = Layout;

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, users, selectUser } = useAuth();
  const { resetDemo } = useDemo();
  const location = useLocation();
  const navigate = useNavigate();
  const reviewer = user.role === "reviewer" || user.role === "admin";
  const menuItems = reviewer
    ? [
        { key: "/reviewer", icon: <AuditOutlined />, label: "待复核队列" },
        { key: "/reviewer/history", icon: <HistoryOutlined />, label: "复核记录" },
      ]
    : [
        { key: "/community", icon: <HomeOutlined />, label: "社区首页" },
        { key: "/my-posts", icon: <UserOutlined />, label: "我的发布" },
        { key: "/appeals", icon: <FileDoneOutlined />, label: "我的申诉" },
      ];

  const activeKey = location.pathname.startsWith("/topics/") ? "/community"
    : location.pathname.startsWith("/reviewer/history") ? "/reviewer/history"
    : location.pathname.startsWith("/reviewer") ? "/reviewer"
    : location.pathname;

  return (
    <Layout className="app-layout">
      <Sider width={236} collapsedWidth={76} collapsed={collapsed} className="app-sider" breakpoint="lg">
        <div className="brand">
          <div className="brand-mark"><SafetyCertificateOutlined /></div>
          {!collapsed && <div><Typography.Text className="brand-name">言鉴 AI</Typography.Text><Typography.Text className="brand-subtitle">ContextGuard · 语境有据</Typography.Text></div>}
        </div>
        {!collapsed && <div className="community-chip"><CommentOutlined /><span>AI Native 青年社区</span></div>}
        <Menu mode="inline" theme="dark" selectedKeys={[activeKey]} items={menuItems} onClick={({ key }) => navigate(key)} className="app-menu" />
        <div className={`demo-meta ${collapsed ? "demo-meta-collapsed" : ""}`}>
          {!collapsed && <><Tag color="geekblue">INTERACTIVE DEMO</Tag><span>前端本地数据 · 可随时重置</span></>}
          <Tooltip title="重置演示数据"><Button type="text" icon={<ReloadOutlined />} onClick={() => { resetDemo(); navigate(reviewer ? "/reviewer" : "/community"); }} /></Tooltip>
        </div>
      </Sider>
      <Layout>
        <Header className="app-header">
          <div className="header-navigation">
            <Button type="text" className="desktop-sider-toggle" icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed((value) => !value)} />
            <div className="header-context"><span className="context-dot" /><Typography.Text>单社区 · 多话题 · 发布前审核</Typography.Text></div>
            <div className="mobile-nav">
              {menuItems.map((item) => <Tooltip title={item.label} key={item.key}><Button type={activeKey === item.key ? "primary" : "text"} icon={item.icon} onClick={() => navigate(item.key)} /></Tooltip>)}
            </div>
          </div>
          <Space size={12} className="user-switcher">
            <div className="identity-copy"><Typography.Text type="secondary">当前演示身份</Typography.Text><Typography.Text strong>{reviewer ? "审核员端" : "普通用户端"}</Typography.Text></div>
            <Select
              value={user.id}
              onChange={(value) => {
                selectUser(value);
                const next = users.find((item) => item.id === value);
                navigate(next?.role === "user" ? "/community" : "/reviewer");
              }}
              options={users.map((item) => ({ label: `${item.displayName} · ${item.role === "user" ? "普通用户" : "审核员"}`, value: item.id }))}
              popupMatchSelectWidth={235}
              className="identity-select"
            />
            <Avatar className={reviewer ? "reviewer-avatar" : "user-avatar"}>{user.displayName.slice(0, 1)}</Avatar>
          </Space>
        </Header>
        <Content className="app-content"><Outlet /></Content>
      </Layout>
    </Layout>
  );
}
