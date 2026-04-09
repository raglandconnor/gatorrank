import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { buildQueryString } from '@/lib/api/http';
import {
  deleteProject,
  getProjectByIdForViewer,
  listProjectsPublic,
} from '@/lib/api/projects';

const { requestJsonMock, requestVoidMock } = vi.hoisted(() => ({
  requestJsonMock: vi.fn(),
  requestVoidMock: vi.fn(),
}));

vi.mock('@/lib/api/request', () => ({
  requestJson: requestJsonMock,
  requestVoid: requestVoidMock,
}));

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
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestVoidMock.mockReset();
    requestJsonMock.mockResolvedValue(LIST_RESPONSE_FIXTURE);
  });

  test('uses anonymous request layer path with no auth refresh behavior', async () => {
    const result = await listProjectsPublic();

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/projects', {
      auth: 'none',
      method: 'GET',
      cache: 'no-store',
      fallbackErrorMessage: 'Failed to fetch projects',
    });
    expect(result).toEqual(LIST_RESPONSE_FIXTURE);
  });

  test('appends query string from the same shape as authenticated listProjects', async () => {
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

    expect(requestJsonMock).toHaveBeenCalledWith(`/api/v1/projects${qs}`, {
      auth: 'none',
      method: 'GET',
      cache: 'no-store',
      fallbackErrorMessage: 'Failed to fetch projects',
    });
  });
});

describe('getProjectByIdForViewer', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestVoidMock.mockReset();
    requestJsonMock.mockResolvedValue(PROJECT_DETAIL_FIXTURE);
    requestVoidMock.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('uses anonymous request when access token is missing', async () => {
    const result = await getProjectByIdForViewer('p1', null);

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/projects/p1', {
      auth: 'none',
      method: 'GET',
      cache: 'no-store',
      fallbackErrorMessage: 'Failed to fetch project',
    });
    expect(result.id).toBe('p1');
  });

  test('uses required-auth request path when access token exists', async () => {
    const result = await getProjectByIdForViewer('p1', 'token-1');

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/projects/p1', {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch project',
    });
    expect(result.slug).toBe('demo-project');
  });

  test('deleteProject delegates to requestVoid with required auth', async () => {
    await deleteProject('p1');

    expect(requestVoidMock).toHaveBeenCalledWith('/api/v1/projects/p1', {
      auth: 'required',
      method: 'DELETE',
      fallbackErrorMessage: 'Failed to delete project',
    });
  });

  test('deleteProject propagates typed errors from requestVoid', async () => {
    requestVoidMock.mockRejectedValue(
      Object.assign(new Error('Project access forbidden'), { status: 403 }),
    );

    await expect(deleteProject('p1')).rejects.toMatchObject({
      message: 'Project access forbidden',
      status: 403,
    });
  });
});
