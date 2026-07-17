import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("contextguard.accessToken");
  if (token) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (error.code === "ECONNABORTED") return "请求超时，请稍后重试";
    if (!error.response) return "无法连接后端服务，请确认 FastAPI 已启动";
  }
  return error instanceof Error ? error.message : "请求失败，请稍后重试";
}
