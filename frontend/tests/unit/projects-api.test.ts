import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { buildQueryString } from '@/lib/api/http';
import {
  getProjectByIdForViewer,
  listProjectsPublic,
} from '@/lib/api/projects';

const { fetchWithAuthMock } = vi.hoisted(() => ({
  fetchWithAuthMock: vi.fn(),
}));

vi.mock('@/lib/api/fetchWithAuth', () => ({
  fetchWithAuth: fetchWithAuthMock,
}));

const originalEnv = process.env.NEXT_PUBLIC_API_BASE_URL;

const PROJECT_DETAIL_FIXTURE = {
  id: 'p1',
  created_by_id: 'u1',
  title: 'Demo Project',
  slug: 'demo-project',
  short_description: 'Short desc',
  long_description: 'Long desc',
  demo_url: null,
  github_url: null,
  video_url: null,
  timeline_start_date: null,
  timeline_end_date: null,
  vote_count: 7,
  team_size: 2,
  is_group_project: true,
  is_published: true,
  viewer_has_voted: false,
  published_at: null,
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
  categories: [],
  tags: [],
  tech_stack: [],
  members: [],
};

const LIST_RESPONSE_FIXTURE = {
  items: [],
  next_cursor: null as string | null,
};

describe('listProjectsPublic', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    fetchWithAuthMock.mockReset();
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('uses plain fetch with absolute apiUrl and never fetchWithAuth', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(LIST_RESPONSE_FIXTURE), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await listProjectsPublic();

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/projects',
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    );
    expect(result.items).toEqual([]);
    expect(result.next_cursor).toBeNull();
  });

  test('appends query string from the same shape as authenticated listProjects', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(LIST_RESPONSE_FIXTURE), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const query = {
      sort: 'top' as const,
      limit: 5,
      published_from: '2026-04-01',
      published_to: '2026-04-30',
    };
    const qs = buildQueryString({
      limit: query.limit,
      cursor: undefined,
      sort: query.sort,
      published_from: query.published_from,
      published_to: query.published_to,
    });

    await listProjectsPublic(query);

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith(
      `http://localhost:8000/api/v1/projects${qs}`,
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    );
  });
});

describe('getProjectByIdForViewer', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
    vi.restoreAllMocks();
    fetchWithAuthMock.mockReset();
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalEnv;
  });

  test('uses anonymous fetch when access token is missing', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(PROJECT_DETAIL_FIXTURE), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await getProjectByIdForViewer('p1', null);

    expect(fetchWithAuthMock).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/projects/p1',
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    );
    expect(result.id).toBe('p1');
  });

  test('uses refresh-aware fetchWithAuth when access token exists', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify(PROJECT_DETAIL_FIXTURE), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await getProjectByIdForViewer('p1', 'token-1');

    expect(fetchWithAuthMock).toHaveBeenCalledWith('/api/v1/projects/p1');
    expect(result.slug).toBe('demo-project');
  });
});
