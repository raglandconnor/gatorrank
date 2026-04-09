import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { fetchWithAuth } from '@/lib/api/fetchWithAuth';

const {
  refreshAuthTokenRawMock,
  clearAuthSessionMock,
  getStoredAccessTokenMock,
  getStoredRefreshTokenMock,
  updateTokensMock,
} = vi.hoisted(() => ({
  refreshAuthTokenRawMock: vi.fn(),
  clearAuthSessionMock: vi.fn(),
  getStoredAccessTokenMock: vi.fn(),
  getStoredRefreshTokenMock: vi.fn(),
  updateTokensMock: vi.fn(),
}));

vi.mock('@/lib/api/authRefresh', () => ({
  refreshAuthTokenRaw: refreshAuthTokenRawMock,
}));

vi.mock('@/lib/auth/storage', () => ({
  clearAuthSession: clearAuthSessionMock,
  getStoredAccessToken: getStoredAccessTokenMock,
  getStoredRefreshToken: getStoredRefreshTokenMock,
  updateTokens: updateTokensMock,
}));

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('fetchWithAuth', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    refreshAuthTokenRawMock.mockReset();
    clearAuthSessionMock.mockReset();
    getStoredAccessTokenMock.mockReset();
    getStoredRefreshTokenMock.mockReset();
    updateTokensMock.mockReset();
    getStoredAccessTokenMock.mockReturnValue('access-old');
    getStoredRefreshTokenMock.mockReturnValue('refresh-old');
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('returns immediate non-401 response without refresh', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ ok: true }), { status: 200 }),
      );

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(refreshAuthTokenRawMock).not.toHaveBeenCalled();
    expect(clearAuthSessionMock).not.toHaveBeenCalled();
  });

  test('clears session and returns 401 when refresh token is missing', async () => {
    getStoredRefreshTokenMock.mockReturnValue(null);
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 401 }),
    );

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(401);
    expect(refreshAuthTokenRawMock).not.toHaveBeenCalled();
    expect(clearAuthSessionMock).toHaveBeenCalledTimes(1);
  });

  test('refreshes and retries once on 401', async () => {
    refreshAuthTokenRawMock.mockResolvedValue({
      access_token: 'access-new',
      refresh_token: 'refresh-new',
    });

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 'u1' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(200);
    expect(refreshAuthTokenRawMock).toHaveBeenCalledWith({
      refresh_token: 'refresh-old',
    });
    expect(updateTokensMock).toHaveBeenCalledWith('access-new', 'refresh-new');

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [, secondInit] = fetchMock.mock.calls[1] as [string, RequestInit];
    const secondHeaders = new Headers(secondInit.headers);
    expect(secondHeaders.get('Authorization')).toBe('Bearer access-new');
    expect(clearAuthSessionMock).not.toHaveBeenCalled();
  });

  test('clears session when refresh fails and returns original 401 response', async () => {
    refreshAuthTokenRawMock.mockRejectedValue(
      new Error('Invalid refresh token'),
    );
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 401 }),
    );

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(401);
    expect(clearAuthSessionMock).toHaveBeenCalledTimes(1);
  });

  test('clears session when retry remains unauthorized', async () => {
    refreshAuthTokenRawMock.mockResolvedValue({
      access_token: 'access-new',
      refresh_token: 'refresh-new',
    });

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }));

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(401);
    expect(clearAuthSessionMock).toHaveBeenCalledTimes(1);
  });
});
