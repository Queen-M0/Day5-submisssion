import { App as AntApp, ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { useAuth } from "./context/AuthContext";
import { AppealsPage } from "./pages/AppealsPage";
import { CommunityPage } from "./pages/CommunityPage";
import { ReviewDetailPage } from "./pages/ReviewDetailPage";
import { ReviewerDashboard } from "./pages/ReviewerDashboard";

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user?.role === "user" ? "/community" : "/reviewer"} replace />;
}

export default function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: "#167a5b",
          colorInfo: "#167a5b",
          colorSuccess: "#27825f",
          colorWarning: "#c97812",
          colorError: "#c23b32",
          borderRadius: 6,
          fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
        components: {
          Layout: { bodyBg: "#f4f6f6", headerBg: "#ffffff", siderBg: "#14241f" },
          Menu: { darkItemBg: "#14241f", itemBorderRadius: 5 },
          Button: { borderRadius: 5 },
        },
      }}
    >
      <AntApp>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<HomeRedirect />} />
            <Route path="community" element={<CommunityPage />} />
            <Route path="appeals" element={<AppealsPage />} />
            <Route path="reviewer" element={<ReviewerDashboard />} />
            <Route path="reviewer/:taskId" element={<ReviewDetailPage />} />
          </Route>
          <Route path="*" element={<HomeRedirect />} />
        </Routes>
      </AntApp>
    </ConfigProvider>
  );
}

