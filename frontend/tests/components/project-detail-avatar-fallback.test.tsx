import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import ProjectDetailPage from '@/app/projects/[slug]/page';
import { renderWithChakra } from '@/tests/utils/render';

const {
  replaceMock,
  pushMock,
  paramsRef,
  getProjectByIdForViewerMock,
  getProjectBySlugForViewerMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  pushMock: vi.fn(),
  paramsRef: { value: { slug: 'mattis-lorem-lorem' } },
  getProjectByIdForViewerMock: vi.fn(),
  getProjectBySlugForViewerMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock, push: pushMock, refresh: vi.fn() }),
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

function makeDetail() {
  return {
    id: 'p-mattis-1',
    created_by_id: 'u1',
    title: 'Mattis lorem lorem',
    slug: 'mattis-lorem-lorem',
    short_description: 'Project details',
    long_description: 'Testing avatar fallback behavior on the member cards.',
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
        username: 'avery',
        role: 'owner',
        full_name: 'Avery Hernandez',
        profile_picture_url: 'https://avatar.gatorrank.mock/user-13.png',
      },
      {
        user_id: 'u2',
        username: 'sam',
        role: 'contributor',
        full_name: 'Sam Rivers',
        profile_picture_url: 'https://avatar.gatorrank.mock/user-14.png',
      },
    ],
  };
}

describe('ProjectDetailPage avatar fallback', () => {
  beforeEach(() => {
    replaceMock.mockReset();
    pushMock.mockReset();
    getProjectByIdForViewerMock.mockReset();
    getProjectBySlugForViewerMock.mockReset();
    paramsRef.value = { slug: 'mattis-lorem-lorem' };
  });

  test('falls back to initials for member avatars when profile images fail', async () => {
    getProjectBySlugForViewerMock.mockResolvedValue(makeDetail());

    renderWithChakra(<ProjectDetailPage />);

    const creatorImage = await screen.findByRole('img', {
      name: 'Avery Hernandez',
    });
    const memberImage = screen.getByRole('img', { name: 'Sam Rivers' });

    fireEvent.error(creatorImage);
    fireEvent.error(memberImage);

    await waitFor(() => {
      expect(screen.getByText('AH')).toBeInTheDocument();
      expect(screen.getByText('SR')).toBeInTheDocument();
    });
  });
});
