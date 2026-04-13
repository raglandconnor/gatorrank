import { renderWithChakra } from '@/tests/utils/render';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { waitFor } from '@testing-library/react';
import ProjectDetailPage from '@/app/projects/[slug]/page';

const {
  replaceMock,
  pushMock,
  paramsRef,
  getProjectByIdForViewerMock,
  getProjectBySlugForViewerMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  pushMock: vi.fn(),
  paramsRef: { value: { slug: 'new-q' } },
  getProjectByIdForViewerMock: vi.fn(),
  getProjectBySlugForViewerMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock }),
  useParams: () => paramsRef.value,
}));

vi.mock('@/components/domain/AuthProvider', () => ({
  useAuth: () => ({
    accessToken: null,
    isReady: true,
    user: null,
  }),
}));

vi.mock('@/lib/api/projects', () => ({
  getProjectByIdForViewer: getProjectByIdForViewerMock,
  getProjectBySlugForViewer: getProjectBySlugForViewerMock,
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/UpvoteBox', () => ({
  UpvoteBox: () => <div data-testid="upvote-box" />,
}));

vi.mock('@/components/projects/ProjectLogoPlaceholder', () => ({
  ProjectLogoPlaceholder: () => <div data-testid="project-logo" />,
}));

vi.mock('@/components/ui/FeatureLoadingState', () => ({
  FeatureLoadingState: () => <div data-testid="feature-loading" />,
}));

vi.mock('@/components/ui/UserAvatar', () => ({
  UserAvatar: () => <div data-testid="user-avatar" />,
}));

function makeDetail(slug: string) {
  return {
    id: 'p-new-1',
    created_by_id: 'u1',
    title: 'New ranking',
    slug,
    short_description: 'New sorted result',
    long_description: 'Project details loaded from backend endpoint.',
    demo_url: null,
    github_url: null,
    video_url: null,
    timeline_start_date: null,
    timeline_end_date: null,
    vote_count: 10,
    team_size: 2,
    is_group_project: true,
    is_published: true,
    viewer_has_voted: false,
    published_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
    updated_at: '2026-04-01T00:00:00Z',
    categories: [],
    tags: [],
    tech_stack: [],
    members: [
      {
        user_id: 'u1',
        username: 'owner_one',
        role: 'owner',
        full_name: 'Owner One',
        profile_picture_url: null,
      },
    ],
  };
}

describe('ProjectDetailPage canonical slug behavior', () => {
  beforeEach(() => {
    replaceMock.mockReset();
    pushMock.mockReset();
    getProjectByIdForViewerMock.mockReset();
    getProjectBySlugForViewerMock.mockReset();
    paramsRef.value = { slug: 'new-q' };
  });

  test('redirects to canonical slug when API returns a different slug', async () => {
    getProjectBySlugForViewerMock.mockResolvedValue(makeDetail('new-ranking'));

    renderWithChakra(<ProjectDetailPage />);

    await waitFor(() => {
      expect(getProjectBySlugForViewerMock).toHaveBeenCalledWith('new-q', null);
      expect(replaceMock).toHaveBeenCalledWith('/projects/new-ranking');
    });
  });

  test('does not redirect when slug is already canonical', async () => {
    getProjectBySlugForViewerMock.mockResolvedValue(makeDetail('new-q'));

    renderWithChakra(<ProjectDetailPage />);

    await waitFor(() => {
      expect(getProjectBySlugForViewerMock).toHaveBeenCalledWith('new-q', null);
    });
    expect(replaceMock).not.toHaveBeenCalled();
  });
});
