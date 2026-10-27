import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { User } from "@/types";
import { setToken, clearToken, getToken } from "@/lib/api";
import apiClient from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface LoginResponse {
  access_token: string;
  token_type: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
  refreshUser: () => Promise<void>;
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = useCallback(async (): Promise<void> => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const response = await apiClient.get<User>("/auth/me");
      setUser(response.data);
    } catch {
      // Token is invalid or expired
      clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restore session on mount
  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      setIsLoading(true);
      try {
          const tokenResponse = await apiClient.post<LoginResponse>(
          "/auth/login",
          { email, password }
        );

        setToken(tokenResponse.data.access_token);

        const userResponse = await apiClient.get<User>("/auth/me");
        setUser(userResponse.data);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback((): void => {
    clearToken();
    setUser(null);
    window.location.href = "/login";
  }, []);

  const hasRole = useCallback(
    (...roles: string[]): boolean => {
      if (!user) return false;
      return roles.includes(user.role);
    },
    [user]
  );

  const hasPermission = useCallback(
    (_permission: string): boolean => {
      if (!user) return false;
      return user.role === "system_admin";
    },
    [user]
  );

  const refreshUser = useCallback(async (): Promise<void> => {
    await fetchCurrentUser();
  }, [fetchCurrentUser]);

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    hasRole,
    hasPermission,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

export default AuthContext;
