import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { searchProjects } from '@/lib/api/search';

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('searchProjects api client', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('builds canonical query params and includes auth header', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [],
          next_cursor: null,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
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

    expect(fetchMock).toHaveBeenCalledTimes(1);

    const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(url);

    expect(parsed.origin).toBe('http://localhost:8000');
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

  test('encodes special characters in query terms', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await searchProjects({ q: 'c++ ai tools' });

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(url);
    expect(parsed.searchParams.get('q')).toBe('c++ ai tools');
  });

  test('maps 400/422/500 failures to user-facing messages', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch');

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'Cursor invalid' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    await expect(searchProjects({ q: 'ai' })).rejects.toThrow('Cursor invalid');

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({}), {
        status: 422,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    await expect(searchProjects({ q: 'ai' })).rejects.toThrow(
      'Search parameters are invalid.',
    );

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({}), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    await expect(searchProjects({ q: 'ai' })).rejects.toThrow(
      'Search failed due to a server error.',
    );
  });

  test('omits auth header when no token provided', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ items: [], next_cursor: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await searchProjects({ q: 'project' });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(options.headers).toEqual({});
  });
});
