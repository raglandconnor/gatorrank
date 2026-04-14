import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import CreateProjectPage from '@/app/projects/create/page';
import { renderWithChakra } from '@/tests/utils/render';

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/ProjectForm', () => ({
  ProjectForm: () => <div data-testid="project-form" />,
}));

describe('CreateProjectPage action rows', () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  test('renders top and bottom action rows with cancel and submit buttons', () => {
    renderWithChakra(<CreateProjectPage />);

    const cancelButtons = screen.getAllByRole('button', { name: 'Cancel' });
    const submitButtons = screen.getAllByRole('button', {
      name: 'Submit Project',
    });

    expect(cancelButtons).toHaveLength(2);
    expect(submitButtons).toHaveLength(2);
  });
});
