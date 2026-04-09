import { describe, expect, test, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import TopProjectsPage from '@/app/projects/top/[type]/page';
import type { ProjectListResponse } from '@/lib/api/types/project';
import { renderWithChakra } from '@/tests/utils/render';

const { useParamsMock, listProjectsPublicMock } = vi.hoisted(() => ({
  useParamsMock: vi.fn(),
  listProjectsPublicMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useParams: useParamsMock,
}));

vi.mock('@/lib/api/projects', () => ({
  listProjectsPublic: listProjectsPublicMock,
}));

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children?: ReactNode }) => (
      <div {...props}>{children}</div>
    ),
  },
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/ProjectGridCard', () => ({
  ProjectGridCard: ({
    project,
    rank,
  }: {
    project: { name: string };
    rank: number;
  }) => <div>{`${rank}. ${project.name}`}</div>,
}));

function makeListItem(id: string, title: string) {
  return {
    id,
    created_by_id: 'u1',
    title,
    slug: `${title.toLowerCase().replace(/\s+/g, '-')}-${id}`,
    short_description: `${title} short`,
    long_description: `${title} long`,
    demo_url: null,
    github_url: null,
    video_url: null,
    timeline_start_date: null,
    timeline_end_date: null,
    vote_count: 10,
    team_size: 1,
    is_group_project: false,
    is_published: true,
    viewer_has_voted: false,
    published_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
    updated_at: '2026-04-01T00:00:00Z',
    categories: [],
    tags: [],
    tech_stack: [],
    members: [],
  };
}

function renderPage() {
  return renderWithChakra(<TopProjectsPage />);
}

describe('TopProjectsPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useParamsMock.mockReset();
    listProjectsPublicMock.mockReset();
    useParamsMock.mockReturnValue({ type: 'top-overall' });
  });

  test('loads paginated projects until next_cursor is null and renders combined list', async () => {
    const page1: ProjectListResponse = {
      items: [makeListItem('p1', 'Alpha Project')],
      next_cursor: 'cursor-2',
    };
    const page2: ProjectListResponse = {
      items: [makeListItem('p2', 'Beta Project')],
      next_cursor: null,
    };

    listProjectsPublicMock
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2);

    renderPage();

    await waitFor(() =>
      expect(listProjectsPublicMock).toHaveBeenCalledTimes(2),
    );

    expect(listProjectsPublicMock).toHaveBeenNthCalledWith(
      1,
      expect.objectContaining({
        sort: 'top',
        limit: 50,
        cursor: undefined,
      }),
    );
    expect(listProjectsPublicMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        sort: 'top',
        limit: 50,
        cursor: 'cursor-2',
      }),
    );

    expect(await screen.findByText('1. Alpha Project')).toBeInTheDocument();
    expect(screen.getByText('2. Beta Project')).toBeInTheDocument();
  });

  test('shows guard error when pagination never terminates', async () => {
    const runawayPage: ProjectListResponse = {
      items: [makeListItem('p1', 'Alpha Project')],
      next_cursor: 'still-more',
    };
    listProjectsPublicMock.mockResolvedValue(runawayPage);

    renderPage();

    expect(
      await screen.findByText('Could not load projects.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Too many projects to load at once/),
    ).toBeInTheDocument();

    await waitFor(() =>
      expect(listProjectsPublicMock).toHaveBeenCalledTimes(20),
    );
  });
});
