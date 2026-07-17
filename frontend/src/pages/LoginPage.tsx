import { LockOutlined, SafetyCertificateOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, App, Button, Card, Form, Input, Space, Tag, Typography } from "antd";
import { Navigate, useNavigate } from "react-router-dom";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  const submit = async (values: { username: string; password: string }) => {
    try {
      const user = await login(values.username.trim(), values.password);
      message.success(`欢迎回来，${user.displayName}`);
      navigate(user.role === "user" ? "/community" : "/reviewer", { replace: true });
    } catch (error) { message.error(apiErrorMessage(error)); }
  };
  return <div className="login-page">
    <section className="login-brand-panel"><div className="login-logo"><SafetyCertificateOutlined /></div><Typography.Title>言鉴 AI</Typography.Title><Typography.Title level={2}>让每次审核都有语境、有证据、可申诉</Typography.Title><Typography.Paragraph>MiMo 双模型初审、申诉反证 Agent 与人工终审协作的内容安全系统。</Typography.Paragraph><Space wrap><Tag>上下文审核</Tag><Tag>证据绑定</Tag><Tag>规则版本化</Tag><Tag>Human in the Loop</Tag></Space></section>
    <Card className="login-card" title="登录 ContextGuard">
      <Alert type="info" showIcon message="演示账号" description={<span>普通用户：zhangsan / user123<br />审核员：reviewer / review123</span>} />
      <Form layout="vertical" onFinish={submit} initialValues={{ username: "zhangsan", password: "user123" }}>
        <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input prefix={<UserOutlined />} autoComplete="username" /></Form.Item>
        <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}><Input.Password prefix={<LockOutlined />} autoComplete="current-password" /></Form.Item>
        <Button type="primary" htmlType="submit" block>登录系统</Button>
      </Form>
      <Typography.Paragraph type="secondary" className="login-note">密码使用 PBKDF2-SHA256 哈希保存，登录令牌有效期 12 小时。</Typography.Paragraph>
    </Card>
  </div>;
}
