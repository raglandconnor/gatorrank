import { renderWithChakra } from '@/tests/utils/render';
import { act, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import CreateProjectPage from '@/app/projects/create/page';

const {
  pushMock,
  createProjectMock,
  publishProjectMock,
  addProjectMemberMock,
  projectFormPropsRef,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  createProjectMock: vi.fn(),
  publishProjectMock: vi.fn(),
  addProjectMemberMock: vi.fn(),
  projectFormPropsRef: { current: null as Record<string, unknown> | null },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/ProjectForm', () => ({
  ProjectForm: (props: Record<string, unknown>) => {
    projectFormPropsRef.current = props;
    return <div data-testid="project-form" />;
  },
}));

vi.mock('@/lib/api/projects', () => ({
  createProject: createProjectMock,
  publishProject: publishProjectMock,
  addProjectMember: addProjectMemberMock,
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}));

describe('CreateProjectPage pending member role behavior', () => {
  test('submits pending member role selections after project creation', async () => {
    createProjectMock.mockResolvedValue({
      id: 'project-1',
      slug: 'project-1',
      title: 'Project 1',
      is_published: false,
    });
    publishProjectMock.mockResolvedValue({
      id: 'project-1',
      slug: 'project-1',
      title: 'Project 1',
      is_published: true,
    });
    addProjectMemberMock.mockResolvedValue({
      user_id: 'u-1',
      username: 'alice',
      role: 'maintainer',
      full_name: 'Alice',
      profile_picture_url: null,
    });

    renderWithChakra(<CreateProjectPage />);

    const formProps = () => {
      if (!projectFormPropsRef.current) {
        throw new Error('ProjectForm props were not captured');
      }
      return projectFormPropsRef.current;
    };

    const addResult = await act(async () =>
      (formProps().onAddMember as (email: string) => Promise<{ ok: boolean }>)(
        'alice@ufl.edu',
      ),
    );
    expect(addResult.ok).toBe(true);

    await act(async () => {
      (
        formProps().onUpdatePendingMemberRole as (
          email: string,
          role: string,
        ) => void
      )('alice@ufl.edu', 'maintainer');
    });

    await act(async () => {
      await (formProps().onSubmit as (payload: object) => Promise<void>)({
        title: 'Project 1',
        short_description: 'Project summary',
        demo_url: 'https://example.com',
      });
    });

    await waitFor(() => {
      expect(createProjectMock).toHaveBeenCalledTimes(1);
      expect(publishProjectMock).toHaveBeenCalledWith('project-1');
      expect(addProjectMemberMock).toHaveBeenCalledWith('project-1', {
        email: 'alice@ufl.edu',
        role: 'maintainer',
      });
      expect(pushMock).toHaveBeenCalledWith('/projects/project-1');
    });
  });
});
