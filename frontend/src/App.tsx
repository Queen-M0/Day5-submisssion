import { App as AntApp, ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { Navigate, Route, Routes } from "react-router-dom";
import { Spin } from "antd";
import { AppShell } from "./components/AppShell";
import { useAuth } from "./context/AuthContext";
import { AppealsPage } from "./pages/AppealsPage";
import { CommunityPage } from "./pages/CommunityPage";
import { MyPostsPage } from "./pages/MyPostsPage";
import { ReviewDetailPage } from "./pages/ReviewDetailPage";
import { ReviewHistoryPage } from "./pages/ReviewHistoryPage";
import { ReviewerDashboard } from "./pages/ReviewerDashboard";
import { StatisticsDashboard } from "./pages/StatisticsDashboard";
import { ModerationRulesPage } from "./pages/ModerationRulesPage";
import { TopicDetailPage } from "./pages/TopicDetailPage";
import { LoginPage } from "./pages/LoginPage";

function HomeRedirect() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "user" ? "/community" : "/reviewer"} replace />;
}

function ProtectedShell() {
  const { loading, isAuthenticated } = useAuth();
  if (loading) return <Spin fullscreen tip="正在恢复登录状态…" />;
  return isAuthenticated ? <AppShell /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#3154a5",
          colorInfo: "#3154a5",
          colorSuccess: "#16856a",
          colorWarning: "#c98322",
          colorError: "#c2413b",
          borderRadius: 10,
          fontFamily: "Inter, 'PingFang SC', 'Microsoft YaHei', ui-sans-serif, system-ui, sans-serif",
          colorText: "#172033",
        },
        components: {
          Layout: { bodyBg: "#f5f7fb", headerBg: "rgba(255,255,255,.94)", siderBg: "#101a32" },
          Menu: { darkItemBg: "#101a32", darkItemSelectedBg: "#294a91", itemBorderRadius: 8 },
          Button: { borderRadius: 8, controlHeight: 38 },
          Card: { borderRadiusLG: 12 },
        },
      }}
    >
      <AntApp>
        <Routes>
          <Route path="login" element={<LoginPage />} />
          <Route element={<ProtectedShell />}>
            <Route index element={<HomeRedirect />} />
            <Route path="community" element={<CommunityPage />} />
            <Route path="topics/:topicId" element={<TopicDetailPage />} />
            <Route path="my-posts" element={<MyPostsPage />} />
            <Route path="appeals" element={<AppealsPage />} />
            <Route path="reviewer" element={<ReviewerDashboard />} />
            <Route path="reviewer/history" element={<ReviewHistoryPage />} />
            <Route path="reviewer/statistics" element={<StatisticsDashboard />} />
            <Route path="reviewer/rules" element={<ModerationRulesPage />} />
            <Route path="reviewer/:taskId" element={<ReviewDetailPage />} />
          </Route>
          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </AntApp>
    </ConfigProvider>
  );
}
