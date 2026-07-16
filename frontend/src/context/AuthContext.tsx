import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { getDemoUsers } from "../api";
import type { DemoUser } from "../types";

interface AuthContextValue {
  user: DemoUser | null;
  users: DemoUser[];
  loading: boolean;
  selectUser: (userId: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [user, setUser] = useState<DemoUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDemoUsers()
      .then((items) => {
        setUsers(items);
        const selectedId = localStorage.getItem("contextguard.userId") ?? "student_a";
        const selected = items.find((item) => item.id === selectedId) ?? items[0] ?? null;
        setUser(selected);
        if (selected) localStorage.setItem("contextguard.userId", selected.id);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      users,
      loading,
      selectUser: (userId) => {
        const selected = users.find((item) => item.id === userId) ?? null;
        setUser(selected);
        if (selected) localStorage.setItem("contextguard.userId", selected.id);
      },
    }),
    [loading, user, users],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

