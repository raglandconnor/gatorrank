/**
 * Persists auth tokens in the browser for SPA → FastAPI calls.
 * Production may move refresh tokens to httpOnly cookies (requires backend/BFF changes).
 */
import type { AuthUser } from '@/lib/api/types/auth';

const PREFIX = 'gatorrank_';
const ACCESS = `${PREFIX}access_token`;
const REFRESH = `${PREFIX}refresh_token`;
const USER = `${PREFIX}user`;

function canUseStorage(): boolean {
  return (
    typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
  );
}

export function getStoredAccessToken(): string | null {
  if (!canUseStorage()) return null;
  return localStorage.getItem(ACCESS);
}

export function getStoredRefreshToken(): string | null {
  if (!canUseStorage()) return null;
  return localStorage.getItem(REFRESH);
}

export function getStoredUser(): AuthUser | null {
  if (!canUseStorage()) return null;
  const raw = localStorage.getItem(USER);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setAuthSession(
  accessToken: string,
  refreshToken: string,
  user: AuthUser,
): void {
  if (!canUseStorage()) return;
  localStorage.setItem(ACCESS, accessToken);
  localStorage.setItem(REFRESH, refreshToken);
  localStorage.setItem(USER, JSON.stringify(user));
}

export function updateTokens(accessToken: string, refreshToken: string): void {
  if (!canUseStorage()) return;
  localStorage.setItem(ACCESS, accessToken);
  localStorage.setItem(REFRESH, refreshToken);
}

export function setStoredUser(user: AuthUser): void {
  if (!canUseStorage()) return;
  localStorage.setItem(USER, JSON.stringify(user));
}

export function clearAuthSession(): void {
  if (!canUseStorage()) return;
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
  localStorage.removeItem(USER);
}
