'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  authLogin,
  authLogout,
  authMe,
  authRefresh,
  authSignup,
} from '@/lib/api/auth';
import type { AuthUser } from '@/lib/api/types/auth';
import {
  clearAuthSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  getStoredUser,
  setAuthSession,
  setStoredUser,
  updateTokens,
} from '@/lib/auth/storage';

export interface AuthContextValue {
  user: AuthUser | null;
  accessToken: string | null;
  isReady: boolean;
  login: (
    email: string,
    password: string,
    rememberMe?: boolean,
  ) => Promise<void>;
  signup: (args: {
    email: string;
    password: string;
    fullName?: string;
    rememberMe?: boolean;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      const access = getStoredAccessToken();
      const refresh = getStoredRefreshToken();
      const u = getStoredUser();

      if (access && refresh && u) {
        if (!cancelled) {
          setAccessToken(access);
          setUser(u);
        }
        return;
      }

      if (access && refresh && !u) {
        try {
          const me = await authMe(access);
          if (cancelled) return;
          const authUser: AuthUser = {
            id: me.id,
            email: me.email,
            role: me.role,
            full_name: me.full_name,
            profile_picture_url: me.profile_picture_url,
          };
          setStoredUser(authUser);
          setUser(authUser);
          setAccessToken(access);
        } catch {
          clearAuthSession();
        }
        return;
      }

      if ((access && !refresh) || (!access && refresh)) {
        clearAuthSession();
      }
    }

    void hydrate().finally(() => {
      if (!cancelled) setIsReady(true);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string, rememberMe = false) => {
      const data = await authLogin({
        email: email.trim(),
        password,
        remember_me: rememberMe,
      });
      setAuthSession(data.access_token, data.refresh_token, data.user);
      setAccessToken(data.access_token);
      setUser(data.user);
    },
    [],
  );

  const signup = useCallback(
    async (args: {
      email: string;
      password: string;
      fullName?: string;
      rememberMe?: boolean;
    }) => {
      const data = await authSignup({
        email: args.email.trim(),
        password: args.password,
        full_name: args.fullName?.trim() || undefined,
        remember_me: args.rememberMe ?? false,
      });
      setAuthSession(data.access_token, data.refresh_token, data.user);
      setAccessToken(data.access_token);
      setUser(data.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    const refresh = getStoredRefreshToken();
    if (refresh) {
      try {
        await authLogout({ refresh_token: refresh });
      } catch {
        // Idempotent on server; still clear client session
      }
    }
    clearAuthSession();
    setUser(null);
    setAccessToken(null);
  }, []);

  const refreshSession = useCallback(async () => {
    const refresh = getStoredRefreshToken();
    if (!refresh) return false;
    try {
      const tokens = await authRefresh({ refresh_token: refresh });
      updateTokens(tokens.access_token, tokens.refresh_token);
      setAccessToken(tokens.access_token);
      setUser(tokens.user);
      setStoredUser(tokens.user);
      return true;
    } catch {
      clearAuthSession();
      setUser(null);
      setAccessToken(null);
      return false;
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isReady,
      login,
      signup,
      logout,
      refreshSession,
    }),
    [user, accessToken, isReady, login, signup, logout, refreshSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
