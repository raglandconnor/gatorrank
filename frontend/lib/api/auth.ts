import { requestJson, requestVoid } from '@/lib/api/request';
import type {
  AuthLoginBody,
  AuthLogoutBody,
  AuthMeResponse,
  AuthRefreshBody,
  AuthSignupBody,
  AuthTokenResponse,
} from '@/lib/api/types/auth';

export async function authSignup(
  body: AuthSignupBody,
): Promise<AuthTokenResponse> {
  return requestJson<AuthTokenResponse>('/api/v1/auth/signup', {
    auth: 'none',
    method: 'POST',
    body,
  });
}

export async function authLogin(
  body: AuthLoginBody,
): Promise<AuthTokenResponse> {
  return requestJson<AuthTokenResponse>('/api/v1/auth/login', {
    auth: 'none',
    method: 'POST',
    body,
  });
}

export async function authMe(accessToken: string): Promise<AuthMeResponse> {
  return requestJson<AuthMeResponse>('/api/v1/auth/me', {
    auth: 'none',
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function authRefresh(
  body: AuthRefreshBody,
): Promise<AuthTokenResponse> {
  return requestJson<AuthTokenResponse>('/api/v1/auth/refresh', {
    auth: 'none',
    method: 'POST',
    body,
  });
}

export async function authLogout(body: AuthLogoutBody): Promise<void> {
  await requestVoid('/api/v1/auth/logout', {
    auth: 'none',
    method: 'POST',
    body,
  });
}
