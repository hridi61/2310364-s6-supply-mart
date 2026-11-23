import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../services/auth";
import { setAccessToken, setSessionHandlers } from "../services/http";
import type { User } from "../types";

// loading: সেশন ফিরিয়ে আনা হচ্ছে (তখন "অতিথি" পেজ দেখানো হয় না)
type Status = "loading" | "authed" | "guest";

interface AuthValue {
  user: User | null;
  status: Status;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<User>;
  signup: (email: string, name: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
  can: (permission: string) => boolean;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  const lose = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setStatus("guest");
  }, []);

  useEffect(() => {
    setSessionHandlers({
      onRefreshed: (u) => setUser(u),
      onLost: lose, // মেয়াদ শেষ/ban হলে সার্ভার যা বলে, UI সেটাই মানে
    });
    // পেজ খুলতেই refresh cookie দিয়ে সেশন ফিরিয়ে আনি
    let cancelled = false;
    authApi.refreshSession().then((data) => {
      if (cancelled) return;
      if (data) {
        setUser(data.user);
        setStatus("authed");
      } else {
        setStatus("guest");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [lose]);

  const value = useMemo<AuthValue>(
    () => ({
      user,
      status,
      isAdmin: user?.role === "admin",
      login: async (email, password) => {
        const u = await authApi.login(email, password);
        setUser(u);
        setStatus("authed");
        return u;
      },
      signup: async (email, name, password) => {
        await authApi.signup(email, name, password);
        const u = await authApi.login(email, password);
        setUser(u);
        setStatus("authed");
      },
      logout: async () => {
        try {
          await authApi.logout();
        } finally {
          lose();
        }
      },
      setUser,
      can: (permission) => user?.permissions.includes(permission) ?? false,
    }),
    [user, status, lose],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
