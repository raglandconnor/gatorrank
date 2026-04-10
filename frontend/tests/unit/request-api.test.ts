import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { requestJson, requestVoid } from '@/lib/api/request';

const { fetchWithAuthMock, getStoredAccessTokenMock } = vi.hoisted(() => ({
  fetchWithAuthMock: vi.fn(),
  getStoredAccessTokenMock: vi.fn(),
}));

vi.mock('@/lib/api/fetchWithAuth', () => ({
  fetchWithAuth: fetchWithAuthMock,
}));

vi.mock('@/lib/auth/storage', () => ({
  getStoredAccessToken: getStoredAccessTokenMock,
}));

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('request api core', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    fetchWithAuthMock.mockReset();
    getStoredAccessTokenMock.mockReset();
    getStoredAccessTokenMock.mockReturnValue(null);
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('routes auth=none through anonymous fetch with query params', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await requestJson<{ ok: boolean }>('/api/v1/ping', {
      auth: 'none',
      query: { q: 'hello', page: 2, featured: true },
      method: 'GET',
    });

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(url);
    expect(parsed.pathname).toBe('/api/v1/ping');
    expect(parsed.searchParams.get('q')).toBe('hello');
    expect(parsed.searchParams.get('page')).toBe('2');
    expect(parsed.searchParams.get('featured')).toBe('true');
    expect(options.method).toBe('GET');
    expect(result.ok).toBe(true);
  });

  test('keeps absolute URLs on auth=none and bypasses fetchWithAuth', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await requestJson<{ ok: boolean }>('https://api.example.com/projects', {
      auth: 'none',
      query: { cursor: 'c2' },
      method: 'GET',
    });

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.example.com/projects?cursor=c2',
      expect.objectContaining({ method: 'GET' }),
    );
  });

  test('routes auth=required through fetchWithAuth and normalizes object body', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ created: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await requestJson<{ created: boolean }>('/api/v1/resource', {
      auth: 'required',
      method: 'POST',
      body: { title: 'Demo' },
    });

    expect(fetchWithAuthMock).toHaveBeenCalledTimes(1);
    const [path, init] = fetchWithAuthMock.mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(path).toBe('/api/v1/resource');
    expect(init.method).toBe('POST');
    expect(init.body).toBe(JSON.stringify({ title: 'Demo' }));

    const headers = new Headers(init.headers);
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  test('routes auth=optional to authenticated path only when token exists', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ value: 1 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    getStoredAccessTokenMock.mockReturnValueOnce('token-123');
    await requestJson<{ value: number }>('/api/v1/with-token', {
      auth: 'optional',
    });

    expect(fetchWithAuthMock).toHaveBeenCalledWith(
      '/api/v1/with-token',
      expect.any(Object),
    );

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ value: 2 }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await requestJson<{ value: number }>('/api/v1/no-token', {
      auth: 'optional',
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://localhost:8000/api/v1/no-token');
  });

  test('retries auth=optional anonymously when authenticated attempt returns 401', async () => {
    getStoredAccessTokenMock.mockReturnValueOnce('stale-token');
    fetchWithAuthMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail: 'Invalid token',
        }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await requestJson<{ items: unknown[] }>('/api/v1/projects', {
      auth: 'optional',
      method: 'GET',
      cache: 'no-store',
    });

    expect(fetchWithAuthMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, fallbackInit] = fetchMock.mock.calls[0] as [string, RequestInit];
    const fallbackHeaders = new Headers(fallbackInit.headers);
    expect(fallbackHeaders.get('Authorization')).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/projects',
      expect.objectContaining({
        method: 'GET',
        cache: 'no-store',
      }),
    );
    expect(result.items).toEqual([]);
  });

  test('does not retry auth=optional anonymously for non-401 failures', async () => {
    getStoredAccessTokenMock.mockReturnValueOnce('token-123');
    fetchWithAuthMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Rate limited' }), {
        status: 429,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: false }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      requestJson('/api/v1/projects', {
        auth: 'optional',
        method: 'GET',
      }),
    ).rejects.toMatchObject({
      message: 'Rate limited',
      status: 429,
    });

    expect(fetchWithAuthMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  test('requestVoid retries auth=optional anonymously on 401', async () => {
    getStoredAccessTokenMock.mockReturnValueOnce('stale-token');
    fetchWithAuthMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Invalid token' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(
      requestVoid('/api/v1/projects/p1/vote', {
        auth: 'optional',
        method: 'DELETE',
      }),
    ).resolves.toBeUndefined();

    expect(fetchWithAuthMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/projects/p1/vote',
      expect.objectContaining({
        method: 'DELETE',
      }),
    );
  });

  test('requestVoid accepts 204 responses', async () => {
    fetchWithAuthMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(
      requestVoid('/api/v1/auth/logout', {
        auth: 'required',
        method: 'POST',
      }),
    ).resolves.toBeUndefined();
  });

  test('requestVoid throws typed error with fallback resolver message', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(null, {
        status: 409,
        statusText: '',
      }),
    );

    await expect(
      requestVoid('/api/v1/projects/p1/members/u1', {
        auth: 'required',
        method: 'DELETE',
        fallbackErrorMessage: (res) =>
          res.status === 409
            ? 'Conflict while removing member.'
            : 'Request failed.',
      }),
    ).rejects.toMatchObject({
      message: 'Conflict while removing member.',
      status: 409,
    });
  });

  test('throws HttpError with parsed backend message and status', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Invalid cursor' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      requestJson('/api/v1/projects', { auth: 'required' }),
    ).rejects.toMatchObject({
      message: 'Invalid cursor',
      status: 400,
    });
  });

  test('uses fallbackErrorMessage when backend payload is not parseable', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(null, {
        status: 500,
        statusText: '',
      }),
    );

    await expect(
      requestJson('/api/v1/projects', {
        auth: 'required',
        fallbackErrorMessage: 'Search request failed.',
      }),
    ).rejects.toMatchObject({
      message: 'Search request failed.',
      status: 500,
    });
  });

  test('uses fallbackErrorMessage resolver when provided as a function', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(null, {
        status: 422,
        statusText: '',
      }),
    );

    await expect(
      requestJson('/api/v1/projects/search', {
        auth: 'required',
        fallbackErrorMessage: (res) =>
          res.status === 422
            ? 'Search parameters are invalid.'
            : 'Search request failed.',
      }),
    ).rejects.toMatchObject({
      message: 'Search parameters are invalid.',
      status: 422,
    });
  });
});
