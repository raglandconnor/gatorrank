import { refreshAuthTokenRaw } from '@/lib/api/authRefresh';
import { apiUrl } from '@/lib/api/client';
import {
  clearAuthSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  updateTokens,
} from '@/lib/auth/storage';

export interface FetchWithAuthOptions extends Omit<RequestInit, 'headers'> {
  headers?: HeadersInit;
}

/**
 * Single in-flight refresh so parallel 401s (e.g. profile + projects) do not
 * both POST /auth/refresh — the second would use a token already rotated by the first.
 */
let refreshAccessTokenPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = getStoredRefreshToken();
  if (!refresh) {
    throw new Error('Missing refresh token');
  }
  const tokens = await refreshAuthTokenRaw({ refresh_token: refresh });
  updateTokens(tokens.access_token, tokens.refresh_token);
  return tokens.access_token;
}

/**
 * GET/POST/etc. to `/api/v1/...` with Bearer access token.
 * On 401, tries one refresh via stored refresh_token, then retries once.
 * If still unauthorized, clears session and redirects to /login.
 */
export async function fetchWithAuth(
  path: string,
  init: FetchWithAuthOptions = {},
): Promise<Response> {
  const url = path.startsWith('http')
    ? path
    : apiUrl(path.startsWith('/') ? path : `/${path}`);

  const doFetch = (accessToken: string | null) => {
    const headers = new Headers(init.headers);
    if (typeof init.body === 'string' && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }
    return fetch(url, { ...init, headers });
  };

  let access = getStoredAccessToken();
  let res = await doFetch(access);

  if (res.status !== 401) {
    return res;
  }

  const refresh = getStoredRefreshToken();
  if (!refresh) {
    clearAuthSession();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return res;
  }

  try {
    if (!refreshAccessTokenPromise) {
      refreshAccessTokenPromise = refreshAccessToken().finally(() => {
        refreshAccessTokenPromise = null;
      });
    }
    access = await refreshAccessTokenPromise;
    res = await doFetch(access);
    if (res.status === 401) {
      clearAuthSession();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  } catch {
    clearAuthSession();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  return res;
}
