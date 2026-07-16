import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api",
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const userId = localStorage.getItem("contextguard.userId") ?? "student_a";
  config.headers.set("X-User-Id", userId);
  return config;
});

