import { createContext, type ReactNode, useContext, useMemo, useState } from "react";
import type { DemoUser } from "../types";

interface AuthContextValue {
  user: DemoUser;
  users: DemoUser[];
  loading: boolean;
  selectUser: (userId: string) => void;
}

const demoUsers: DemoUser[] = [
  { id: "student_a", username: "zhangsan", displayName: "张三", role: "user" },
  { id: "student_b", username: "lisi", displayName: "李四", role: "user" },
  { id: "student_c", username: "wangwu", displayName: "王五", role: "user" },
  { id: "reviewer_1", username: "reviewer", displayName: "审核员", role: "reviewer" },
];

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState(() => localStorage.getItem("contextguard.userId") ?? "student_a");
  const user = demoUsers.find((item) => item.id === userId) ?? demoUsers[0];
  const value = useMemo<AuthContextValue>(() => ({
    user,
    users: demoUsers,
    loading: false,
    selectUser: (nextUserId) => {
      localStorage.setItem("contextguard.userId", nextUserId);
      setUserId(nextUserId);
    },
  }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
