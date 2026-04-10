import { screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { SearchResultRow } from '@/components/projects/SearchResultRow';
import { renderWithChakra } from '@/tests/utils/render';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe('SearchResultRow', () => {
  test('renders fallback taxonomy/date and project link', () => {
    renderWithChakra(
      <SearchResultRow
        project={{
          id: 'proj-1',
          created_by_id: 'user-1',
          title: 'Test Project',
          slug: 'test-project',
          short_description: 'description',
          long_description: null,
          demo_url: null,
          github_url: null,
          video_url: null,
          timeline_start_date: null,
          timeline_end_date: null,
          vote_count: 4,
          team_size: 1,
          is_group_project: false,
          is_published: true,
          viewer_has_voted: false,
          published_at: null,
          created_at: '2026-04-01T00:00:00Z',
          updated_at: '2026-04-01T00:00:00Z',
          categories: [{ id: 'cat-1', name: 'AI' }],
          tags: [],
          tech_stack: [],
          members: [],
        }}
      />,
    );

    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
    expect(screen.getByText('Unpublished')).toBeInTheDocument();

    const link = screen.getByRole('link', { name: /Test Project/i });
    expect(link).toHaveAttribute('href', '/projects/proj-1');
  });
});
