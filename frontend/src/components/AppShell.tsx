import {
  AuditOutlined,
  BarChartOutlined,
  CommentOutlined,
  FileDoneOutlined,
  HistoryOutlined,
  HomeOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ReloadOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Alert, Avatar, Button, Layout, Menu, Space, Spin, Tag, Tooltip, Typography } from "antd";
import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useDemo } from "../context/DemoContext";

const { Header, Sider, Content } = Layout;

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const { resetDemo, loading, error } = useDemo();
  const location = useLocation();
  const navigate = useNavigate();
  const reviewer = user.role === "reviewer" || user.role === "admin";
  const menuItems = reviewer
    ? [
        { key: "/reviewer", icon: <AuditOutlined />, label: "待复核队列" },
        { key: "/reviewer/history", icon: <HistoryOutlined />, label: "复核记录" },
        { key: "/reviewer/statistics", icon: <BarChartOutlined />, label: "数据统计看板" },
        { key: "/reviewer/rules", icon: <SettingOutlined />, label: "审核规则配置" },
      ]
    : [
        { key: "/community", icon: <HomeOutlined />, label: "社区首页" },
        { key: "/my-posts", icon: <UserOutlined />, label: "我的发布" },
        { key: "/appeals", icon: <FileDoneOutlined />, label: "我的申诉" },
      ];

  const activeKey = location.pathname.startsWith("/topics/") ? "/community"
    : location.pathname.startsWith("/reviewer/history") ? "/reviewer/history"
    : location.pathname.startsWith("/reviewer/statistics") ? "/reviewer/statistics"
    : location.pathname.startsWith("/reviewer/rules") ? "/reviewer/rules"
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
          {!collapsed && <><Tag color="green">LIVE API</Tag><span>后端数据库实时数据</span></>}
          <Tooltip title="重新读取后端数据"><Button type="text" loading={loading} icon={<ReloadOutlined />} onClick={() => { resetDemo(); navigate(reviewer ? "/reviewer" : "/community"); }} /></Tooltip>
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
            <Tag color={reviewer ? "geekblue" : "green"}>{user.displayName} · {reviewer ? "审核员" : "普通用户"}</Tag>
            <Avatar className={reviewer ? "reviewer-avatar" : "user-avatar"}>{user.displayName.slice(0, 1)}</Avatar>
            <Tooltip title="退出登录"><Button type="text" icon={<LogoutOutlined />} onClick={() => { logout(); navigate("/login", { replace: true }); }} /></Tooltip>
          </Space>
        </Header>
        <Content className="app-content">{error && <Alert type="error" showIcon closable message="后端数据加载失败" description={error} style={{ margin: 20 }} />}<Outlet />{loading && <Spin fullscreen tip="正在读取后端数据…" />}</Content>
      </Layout>
    </Layout>
  );
}
