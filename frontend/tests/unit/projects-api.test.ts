import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { getProjectByIdForViewer } from '@/lib/api/projects';

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
