'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import type { AuthUser } from '@/lib/api/types/auth';
import { getMe } from '@/lib/api/users';
import { getSupabaseBrowserClient } from '@/lib/supabase/browser';

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
    username: string;
    password: string;
    fullName?: string;
    rememberMe?: boolean;
  }) => Promise<void>;
  logout: () => Promise<void>;
  /** Updates in-memory user cache (e.g. after PATCH /users/me). */
  updateCachedUser: (next: AuthUser) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);

  const syncUserFromBackend = useCallback(async () => {
    const me = await getMe();
    const authUser: AuthUser = {
      id: me.id,
      email: me.email,
      username: me.username,
      role: me.role,
      full_name: me.full_name,
      profile_picture_url: me.profile_picture_url,
    };
    setUser(authUser);
  }, []);

  const handleSessionChange = useCallback(
    async (nextAccessToken: string | null) => {
      setAccessToken(nextAccessToken);
      if (!nextAccessToken) {
        setUser(null);
        return;
      }

      try {
        await syncUserFromBackend();
      } catch {
        setUser(null);
      }
    },
    [syncUserFromBackend],
  );

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      const { data } = await supabase.auth.getSession();
      if (!cancelled) {
        await handleSessionChange(data.session?.access_token ?? null);
      }
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      void handleSessionChange(session?.access_token ?? null);
    });

    void hydrate().finally(() => {
      if (!cancelled) setIsReady(true);
    });

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, [handleSessionChange, supabase.auth]);

  const login = useCallback(
    async (email: string, password: string, rememberMe = false) => {
      void rememberMe;
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (error) {
        throw error;
      }
      await handleSessionChange(data.session?.access_token ?? null);
    },
    [handleSessionChange, supabase.auth],
  );

  const signup = useCallback(
    async (args: {
      email: string;
      username: string;
      password: string;
      fullName?: string;
      rememberMe?: boolean;
    }) => {
      void args.rememberMe;
      const emailRedirectTo =
        typeof window === 'undefined'
          ? undefined
          : `${window.location.origin}/auth/callback?next=/login`;
      const { data, error } = await supabase.auth.signUp({
        email: args.email.trim().toLowerCase(),
        password: args.password,
        options: {
          emailRedirectTo,
          data: {
            username: args.username.trim().toLowerCase(),
            full_name: args.fullName?.trim() || null,
          },
        },
      });
      if (error) {
        throw error;
      }
      await handleSessionChange(data.session?.access_token ?? null);
    },
    [handleSessionChange, supabase.auth],
  );

  const logout = useCallback(async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      throw error;
    }
    setAccessToken(null);
    setUser(null);
  }, [supabase.auth]);

  const updateCachedUser = useCallback((next: AuthUser) => {
    setUser(next);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isReady,
      login,
      signup,
      logout,
      updateCachedUser,
    }),
    [user, accessToken, isReady, login, signup, logout, updateCachedUser],
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
