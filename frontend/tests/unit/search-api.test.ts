import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { searchProjects } from '@/lib/api/search';

const { requestJsonMock } = vi.hoisted(() => ({
  requestJsonMock: vi.fn(),
}));

vi.mock('@/lib/api/request', () => ({
  requestJson: requestJsonMock,
  requestVoid: vi.fn(),
}));

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

describe('searchProjects api client', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestJsonMock.mockResolvedValue({ items: [], next_cursor: null });
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('uses auth request path with canonical query params when token is provided', async () => {
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

    expect(requestJsonMock).toHaveBeenCalledTimes(1);

    const [path, options] = requestJsonMock.mock.calls[0] as [
      string,
      { headers: HeadersInit; fallbackErrorMessage: (res: Response) => string },
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

    expect(options.headers).toEqual({ Authorization: 'Bearer token-123' });
    expect(
      options.fallbackErrorMessage(new Response(null, { status: 422 })),
    ).toBe('Search parameters are invalid.');
    expect(
      options.fallbackErrorMessage(new Response(null, { status: 500 })),
    ).toBe('Search request failed.');
  });

  test('uses anonymous request path when token is absent', async () => {
    await searchProjects({ q: 'project' });

    expect(requestJsonMock).toHaveBeenCalledTimes(1);
    const [url, options] = requestJsonMock.mock.calls[0] as [
      string,
      { auth: string; method: string },
    ];
    expect(url).toContain(
      'http://localhost:8000/api/v1/projects/search?q=project',
    );
    expect(options.auth).toBe('none');
    expect(options.method).toBe('GET');
  });

  test('encodes special characters in query terms', async () => {
    await searchProjects({ q: 'c++ ai tools' }, 'token-123');

    const [path] = requestJsonMock.mock.calls[0] as [string, object];
    const parsed = new URL(`http://example.local${path}`);
    expect(parsed.searchParams.get('q')).toBe('c++ ai tools');
  });
});
