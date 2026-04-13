import type { HTMLAttributes, ReactNode } from 'react';
import { screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import {
  CommentPill,
  VotePill,
} from '@/components/projects/ProjectActionPills';
import { renderWithChakra } from '@/tests/utils/render';

vi.mock('framer-motion', async () => {
  const actual =
    await vi.importActual<typeof import('framer-motion')>('framer-motion');

  return {
    ...actual,
    AnimatePresence: ({ children }: { children: ReactNode }) => children,
    motion: {
      span: ({ children, ...props }: HTMLAttributes<HTMLSpanElement>) => (
        <span {...props}>{children}</span>
      ),
    },
  };
});

describe('ProjectActionPills', () => {
  test('renders a non-interactive comment pill without exposing a button', () => {
    renderWithChakra(
      <CommentPill count={3} ariaLabel="3 comments on GatorRank" />,
    );

    expect(
      screen.queryByRole('button', { name: /3 comments on GatorRank/i }),
    ).toBeNull();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  test('renders a disabled vote pill while pending', () => {
    renderWithChakra(
      <VotePill
        count={12}
        pending
        active
        ariaLabel="Upvote GatorRank"
        onClick={vi.fn()}
      />,
    );

    expect(
      screen.getByRole('button', { name: /Upvote GatorRank/i }),
    ).toBeDisabled();
  });
});
