import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { searchProjects } from '@/lib/api/search';

const { fetchWithAuthMock } = vi.hoisted(() => ({
  fetchWithAuthMock: vi.fn(),
}));

vi.mock('@/lib/api/fetchWithAuth', () => ({
  fetchWithAuth: fetchWithAuthMock,
}));

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('searchProjects api client', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    fetchWithAuthMock.mockReset();
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('uses refresh-aware auth path with canonical query params', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await searchProjects(
      {
        q: ' ai tools ',
        sort: 'new',
        cursor: 'abc123',
        limit: 25,
        categories: ['Software Engineering'],
        tags: ['AI', 'ML'],
        tech_stack: ['TypeScript'],
      },
      'token-123',
    );

    expect(fetchWithAuthMock).toHaveBeenCalledTimes(1);

    const [path, options] = fetchWithAuthMock.mock.calls[0] as [
      string,
      RequestInit,
    ];

    const parsed = new URL(`http://example.local${path}`);
    expect(parsed.pathname).toBe('/api/v1/projects/search');
    expect(parsed.searchParams.get('q')).toBe('ai tools');
    expect(parsed.searchParams.get('sort')).toBe('new');
    expect(parsed.searchParams.get('cursor')).toBe('abc123');
    expect(parsed.searchParams.get('limit')).toBe('25');
    expect(parsed.searchParams.getAll('categories')).toEqual([
      'Software Engineering',
    ]);
    expect(parsed.searchParams.getAll('tags')).toEqual(['AI', 'ML']);
    expect(parsed.searchParams.getAll('tech_stack')).toEqual(['TypeScript']);
    expect(parsed.searchParams.getAll('categories[]')).toEqual([]);
    expect(parsed.searchParams.getAll('tags[]')).toEqual([]);
    expect(parsed.searchParams.getAll('tech_stack[]')).toEqual([]);

    expect(options.headers).toEqual({ Authorization: 'Bearer token-123' });
  });

  test('uses anonymous fetch path when token is absent', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await searchProjects({ q: 'project' });

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/api/v1/projects/search?q=project');
    expect(options.method).toBe('GET');
  });

  test('encodes special characters in query terms', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ items: [], next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await searchProjects({ q: 'c++ ai tools' }, 'token-123');

    const [path] = fetchWithAuthMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(`http://example.local${path}`);
    expect(parsed.searchParams.get('q')).toBe('c++ ai tools');
  });

  test('surfaces backend error details/status for 400/422/500', async () => {
    fetchWithAuthMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: 'Cursor invalid' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({}), {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({}), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          statusText: 'Internal Server Error',
        }),
      );

    await expect(
      searchProjects({ q: 'ai' }, 'token-123'),
    ).rejects.toMatchObject({
      message: 'Cursor invalid',
      status: 400,
    });

    await expect(
      searchProjects({ q: 'ai' }, 'token-123'),
    ).rejects.toMatchObject({
      message: 'Search parameters are invalid.',
      status: 422,
    });

    await expect(
      searchProjects({ q: 'ai' }, 'token-123'),
    ).rejects.toMatchObject({
      message: 'Internal Server Error',
      status: 500,
    });
  });
});
