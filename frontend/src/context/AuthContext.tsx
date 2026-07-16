import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { getDemoUsers } from "../api";
import type { DemoUser } from "../types";

interface AuthContextValue {
  user: DemoUser;
  users: DemoUser[];
  loading: boolean;
  selectUser: (userId: string) => void;
}

const fallbackUsers: DemoUser[] = [
  { id: "student_a", username: "zhangsan", displayName: "张三", role: "user" },
  { id: "student_b", username: "lisi", displayName: "李四", role: "user" },
  { id: "student_c", username: "wangwu", displayName: "王五", role: "user" },
  { id: "reviewer_1", username: "reviewer", displayName: "审核员", role: "reviewer" },
];

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<DemoUser[]>(fallbackUsers);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(() => localStorage.getItem("contextguard.userId") ?? "student_a");

  useEffect(() => {
    let active = true;
    getDemoUsers()
      .then((items) => {
        if (!active || items.length === 0) return;
        setUsers(items);
        if (!items.some((item) => item.id === userId)) {
          localStorage.setItem("contextguard.userId", items[0].id);
          setUserId(items[0].id);
        }
      })
      .catch(() => undefined)
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [userId]);

  const user = users.find((item) => item.id === userId) ?? users[0];
  const value = useMemo<AuthContextValue>(() => ({
    user,
    users,
    loading,
    selectUser: (nextUserId) => {
      localStorage.setItem("contextguard.userId", nextUserId);
      setUserId(nextUserId);
    },
  }), [loading, user, users]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
