import { screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { ProjectCard } from '@/components/projects/ProjectCard';
import { ProjectGridCard } from '@/components/projects/ProjectGridCard';
import { renderWithChakra } from '@/tests/utils/render';

vi.mock('@/hooks/useProjectVote', () => ({
  useProjectVote: () => ({
    isVoted: false,
    voteCount: 12,
    isPending: false,
    toggleVote: vi.fn(),
  }),
}));

function projectFixture() {
  return {
    id: 'proj-1',
    name: 'GatorRank',
    slug: 'gatorrank',
    description: 'Project ranking platform.',
    tags: ['React', 'TypeScript'],
    votes: 12,
    viewerHasVoted: false,
    comments: 3,
  };
}

function projectWithoutTagsFixture() {
  return {
    ...projectFixture(),
    name: 'Campus Compass',
    slug: 'campus-compass',
    tags: [],
  };
}

describe('project card navigation', () => {
  test('ProjectCard renders a semantic link to the canonical project route', () => {
    renderWithChakra(<ProjectCard project={projectFixture()} rank={1} />);

    const link = screen.getByRole('link', { name: /1\. GatorRank/i });
    expect(link).toHaveAttribute('href', '/projects/gatorrank');

    const commentButton = screen.getByRole('button', {
      name: /3 comments on GatorRank/i,
    });
    const upvoteButton = screen.getByRole('button', {
      name: /Upvote GatorRank/i,
    });
    expect(commentButton.closest('a')).toBeNull();
    expect(upvoteButton.closest('a')).toBeNull();
  });

  test('ProjectGridCard renders a semantic link to the canonical project route', () => {
    renderWithChakra(<ProjectGridCard project={projectFixture()} rank={2} />);

    const link = screen.getByRole('link', { name: /2\. GatorRank/i });
    expect(link).toHaveAttribute('href', '/projects/gatorrank');

    const commentButton = screen.getByRole('button', {
      name: /3 comments on GatorRank/i,
    });
    const upvoteButton = screen.getByRole('button', {
      name: /Upvote GatorRank/i,
    });

    expect(commentButton.closest('a')).toBeNull();
    expect(upvoteButton.closest('a')).toBeNull();
  });

  test('cards with no tags do not render a fallback Project tag', () => {
    const noTagsProject = projectWithoutTagsFixture();

    renderWithChakra(
      <>
        <ProjectCard project={noTagsProject} rank={1} />
        <ProjectGridCard project={noTagsProject} rank={2} />
      </>,
    );

    expect(screen.queryByText(/^Project$/)).not.toBeInTheDocument();
  });
});
