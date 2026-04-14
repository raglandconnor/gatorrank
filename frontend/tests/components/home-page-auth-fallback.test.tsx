import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import Home from '@/app/page';
import { renderWithChakra } from '@/tests/utils/render';

const { fetchWithAuthMock } = vi.hoisted(() => ({
  fetchWithAuthMock: vi.fn(),
}));

vi.mock('@/lib/api/fetchWithAuth', () => ({
  fetchWithAuth: fetchWithAuthMock,
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/ProjectSection', () => ({
  ProjectSection: ({
    title,
    projects,
  }: {
    title: string;
    projects: Array<{ id: string | number; name: string }>;
  }) => (
    <section>
      <h2>{title}</h2>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>{project.name}</li>
        ))}
      </ul>
    </section>
  ),
}));

function projectListPayload(title: string) {
  return {
    items: [
      {
        id: `${title.toLowerCase().replace(/\s+/g, '-')}-1`,
        created_by_id: 'u1',
        title,
        slug: title.toLowerCase().replace(/\s+/g, '-'),
        short_description: `${title} description`,
        long_description: null,
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
        published_at: '2026-04-01T00:00:00Z',
        created_at: '2026-04-01T00:00:00Z',
        updated_at: '2026-04-01T00:00:00Z',
        categories: [],
        tags: [],
        tech_stack: [],
        members: [],
      },
    ],
    next_cursor: null,
  };
}

describe('Home optional-auth fallback behavior', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    fetchWithAuthMock.mockReset();

    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  });

  test('renders public sections when optional-auth requests get 401 and fall back anonymously', async () => {
    fetchWithAuthMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Invalid token' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(projectListPayload('Overall Winner')), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(projectListPayload('This Month Winner')), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(projectListPayload('Last Month Winner')), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );

    renderWithChakra(<Home />);

    await waitFor(() => {
      expect(fetchWithAuthMock).toHaveBeenCalledTimes(3);
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    expect(await screen.findByText('Overall Winner')).toBeInTheDocument();
    expect(screen.getByText('This Month Winner')).toBeInTheDocument();
    expect(screen.getByText('Last Month Winner')).toBeInTheDocument();
    expect(
      screen.queryByText('Could not load home projects.'),
    ).not.toBeInTheDocument();
  });
});
