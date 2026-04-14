import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

const { getSupabaseBrowserClientMock, getSessionMock } = vi.hoisted(() => ({
  getSupabaseBrowserClientMock: vi.fn(),
  getSessionMock: vi.fn(),
}));

vi.mock('@/lib/supabase/browser', () => ({
  getSupabaseBrowserClient: getSupabaseBrowserClientMock,
}));

import { fetchWithAuth } from '@/lib/api/fetchWithAuth';

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('fetchWithAuth', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    getSupabaseBrowserClientMock.mockReset();
    getSessionMock.mockReset();
    getSupabaseBrowserClientMock.mockReturnValue({
      auth: {
        getSession: getSessionMock,
      },
    });
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('uses Supabase access token when session exists', async () => {
    getSessionMock.mockResolvedValue({
      data: {
        session: {
          access_token: 'supabase-access',
        },
      },
      error: null,
    });

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ ok: true }), { status: 200 }),
      );

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(headers.get('Authorization')).toBe('Bearer supabase-access');
  });

  test('omits Authorization header when session is missing', async () => {
    getSessionMock.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(null, { status: 401 }));

    const res = await fetchWithAuth('/api/v1/users/me');

    expect(res.status).toBe(401);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(headers.get('Authorization')).toBeNull();
  });

  test('passes absolute URLs through unchanged', async () => {
    getSessionMock.mockResolvedValue({
      data: {
        session: {
          access_token: 'supabase-access',
        },
      },
      error: null,
    });

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(JSON.stringify({ ok: true }), { status: 200 }),
      );

    await fetchWithAuth('https://api.example.com/v1/users/me');

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://api.example.com/v1/users/me');
  });
});
