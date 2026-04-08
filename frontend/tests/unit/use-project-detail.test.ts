import { describe, expect, test, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProjectDetail } from '@/app/projects/[projectId]/_hooks/useProjectDetail';

const { getProjectByIdForViewerMock } = vi.hoisted(() => ({
  getProjectByIdForViewerMock: vi.fn(),
}));

vi.mock('@/lib/api/projects', () => ({
  getProjectByIdForViewer: getProjectByIdForViewerMock,
}));

describe('useProjectDetail', () => {
  beforeEach(() => {
    getProjectByIdForViewerMock.mockReset();
  });

  test('loads and maps project detail successfully', async () => {
    getProjectByIdForViewerMock.mockResolvedValue({
      id: 'p1',
      created_by_id: 'u1',
      title: 'Demo Project',
      slug: 'demo-project',
      short_description: 'Short desc',
      long_description: 'Long desc',
      demo_url: 'https://demo.example.com',
      github_url: 'https://github.com/org/repo',
      video_url: 'https://youtu.be/dQw4w9WgXcQ',
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
      categories: [{ id: 'c1', name: 'AI' }],
      tags: [{ id: 't1', name: 'Next.js' }],
      tech_stack: [],
      members: [
        {
          id: 'm1',
          project_id: 'p1',
          user_id: 'u1',
          role: 'owner',
          joined_at: '2026-04-01T00:00:00Z',
          full_name: 'Owner Name',
          username: 'owner',
          profile_picture_url: null,
        },
      ],
    });

    const { result } = renderHook(() => useProjectDetail('p1', 'token', true));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(getProjectByIdForViewerMock).toHaveBeenCalledWith('p1', 'token');
    expect(result.current.notFound).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.project?.name).toBe('Demo Project');
    expect(result.current.project?.tags).toEqual(['Next.js']);
    expect(result.current.projectCreator?.role).toBe('owner');
  });

  test('sets notFound for 404 responses', async () => {
    const notFoundError = Object.assign(new Error('Not found'), {
      status: 404,
    });
    getProjectByIdForViewerMock.mockRejectedValue(notFoundError);

    const { result } = renderHook(() => useProjectDetail('p404', null, true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.notFound).toBe(true);
    expect(result.current.project).toBeNull();
    expect(result.current.error).toBeNull();
  });

  test('sets generic error message for non-404 failures', async () => {
    getProjectByIdForViewerMock.mockRejectedValue(new Error('Network failed'));

    const { result } = renderHook(() => useProjectDetail('p2', null, true));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.notFound).toBe(false);
    expect(result.current.project).toBeNull();
    expect(result.current.error).toBe('Network failed');
  });
});
