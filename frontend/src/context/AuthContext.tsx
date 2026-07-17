import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, getDemoUsers, login as loginRequest } from "../api";
import type { DemoUser } from "../types";

interface AuthContextValue {
  user: DemoUser;
  users: DemoUser[];
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<DemoUser>;
  logout: () => void;
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
  const [user, setUser] = useState<DemoUser>(fallbackUsers[0]);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem("contextguard.accessToken");
    if (!token) { setLoading(false); return () => { active = false; }; }
    Promise.all([getCurrentUser(), getDemoUsers()])
      .then(([current, items]) => {
        if (!active) return;
        setUser(current);
        if (items.length) setUsers(items);
        setAuthenticated(true);
      })
      .catch(() => {
        localStorage.removeItem("contextguard.accessToken");
        localStorage.removeItem("contextguard.userId");
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    users,
    loading,
    isAuthenticated,
    login: async (username, password) => {
      const result = await loginRequest({ username, password });
      localStorage.setItem("contextguard.accessToken", result.accessToken);
      localStorage.setItem("contextguard.userId", result.user.id);
      setUser(result.user);
      setAuthenticated(true);
      getDemoUsers().then((items) => items.length && setUsers(items)).catch(() => undefined);
      return result.user;
    },
    logout: () => {
      localStorage.removeItem("contextguard.accessToken");
      localStorage.removeItem("contextguard.userId");
      setAuthenticated(false);
      setUser(fallbackUsers[0]);
    },
  }), [isAuthenticated, loading, user, users]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
