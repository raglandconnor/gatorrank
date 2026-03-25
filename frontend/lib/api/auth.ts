import { apiUrl } from '@/lib/api/client';
import type {
  AuthLoginBody,
  AuthLogoutBody,
  AuthMeResponse,
  AuthRefreshBody,
  AuthSignupBody,
  AuthTokenResponse,
} from '@/lib/api/types/auth';

async function parseErrorMessage(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown };
    const d = data.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) {
      const first = d[0] as { msg?: string } | undefined;
      if (first?.msg) return first.msg;
    }
    return res.statusText || 'Request failed';
  } catch {
    return res.statusText || 'Request failed';
  }
}

export async function authSignup(
  body: AuthSignupBody,
): Promise<AuthTokenResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/signup'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res));
  }
  return res.json() as Promise<AuthTokenResponse>;
}

export async function authLogin(
  body: AuthLoginBody,
): Promise<AuthTokenResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res));
  }
  return res.json() as Promise<AuthTokenResponse>;
}

export async function authMe(accessToken: string): Promise<AuthMeResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/me'), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res));
  }
  return res.json() as Promise<AuthMeResponse>;
}

export async function authRefresh(
  body: AuthRefreshBody,
): Promise<AuthTokenResponse> {
  const res = await fetch(apiUrl('/api/v1/auth/refresh'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res));
  }
  return res.json() as Promise<AuthTokenResponse>;
}

export async function authLogout(body: AuthLogoutBody): Promise<void> {
  const res = await fetch(apiUrl('/api/v1/auth/logout'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(await parseErrorMessage(res));
  }
}
