import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import EditProjectPage from '@/app/projects/[slug]/edit/page';
import { renderWithChakra } from '@/tests/utils/render';

const {
  replaceMock,
  pushMock,
  refreshMock,
  paramsRef,
  getProjectMock,
  getProjectBySlugMock,
  updateProjectMock,
  publishProjectMock,
  unpublishProjectMock,
  addProjectMemberMock,
  removeProjectMemberMock,
  deleteProjectMock,
  toastSuccessMock,
  toastErrorMock,
} = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  paramsRef: { value: { slug: 'demo-project' } },
  getProjectMock: vi.fn(),
  getProjectBySlugMock: vi.fn(),
  updateProjectMock: vi.fn(),
  publishProjectMock: vi.fn(),
  unpublishProjectMock: vi.fn(),
  addProjectMemberMock: vi.fn(),
  removeProjectMemberMock: vi.fn(),
  deleteProjectMock: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: replaceMock,
    push: pushMock,
    refresh: refreshMock,
  }),
  useParams: () => paramsRef.value,
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/projects/ProjectForm', () => ({
  ProjectForm: () => <div data-testid="project-form" />,
}));

vi.mock('@/lib/api/projects', () => ({
  getProject: getProjectMock,
  getProjectBySlug: getProjectBySlugMock,
  updateProject: updateProjectMock,
  publishProject: publishProjectMock,
  unpublishProject: unpublishProjectMock,
  addProjectMember: addProjectMemberMock,
  removeProjectMember: removeProjectMemberMock,
  deleteProject: deleteProjectMock,
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  },
}));

function makeProjectDetail() {
  return {
    id: 'project-1',
    created_by_id: 'user-1',
    title: 'Demo Project',
    slug: 'demo-project',
    short_description: 'Short project summary',
    long_description: 'Long description',
    demo_url: 'https://example.com/demo',
    github_url: 'https://github.com/example/demo',
    video_url: null,
    timeline_start_date: null,
    timeline_end_date: null,
    vote_count: 4,
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

describe('EditProjectPage delete flow', () => {
  beforeEach(() => {
    replaceMock.mockReset();
    pushMock.mockReset();
    refreshMock.mockReset();
    getProjectMock.mockReset();
    getProjectBySlugMock.mockReset();
    updateProjectMock.mockReset();
    publishProjectMock.mockReset();
    unpublishProjectMock.mockReset();
    addProjectMemberMock.mockReset();
    removeProjectMemberMock.mockReset();
    deleteProjectMock.mockReset();
    toastSuccessMock.mockReset();
    toastErrorMock.mockReset();
    paramsRef.value = { slug: 'demo-project' };
    getProjectBySlugMock.mockResolvedValue(makeProjectDetail());
  });

  test('requires typed title (case-insensitive, trimmed) before enabling delete', async () => {
    renderWithChakra(<EditProjectPage />);

    await screen.findByText('Delete project');
    fireEvent.click(screen.getByRole('button', { name: 'Delete Project' }));

    const input = screen.getByLabelText(
      'Type project title to confirm deletion',
    );
    const deleteButton = screen.getAllByRole('button', {
      name: 'Delete Project',
    })[1];

    expect(deleteButton).toBeDisabled();

    fireEvent.change(input, { target: { value: '  DEMO PROJECT  ' } });
    expect(deleteButton).toBeEnabled();
  });

  test('renders top and bottom action rows with cancel and save buttons', async () => {
    renderWithChakra(<EditProjectPage />);

    await screen.findByText('Delete project');

    const cancelButtons = screen.getAllByRole('button', { name: 'Cancel' });
    const saveButtons = screen.getAllByRole('button', { name: 'Save Changes' });

    expect(cancelButtons).toHaveLength(2);
    expect(saveButtons).toHaveLength(2);
  });

  test('deletes project, shows success toast, and redirects to profile', async () => {
    deleteProjectMock.mockResolvedValue(undefined);
    renderWithChakra(<EditProjectPage />);

    await screen.findByText('Delete project');
    fireEvent.click(screen.getByRole('button', { name: 'Delete Project' }));
    fireEvent.change(
      screen.getByLabelText('Type project title to confirm deletion'),
      { target: { value: 'demo project' } },
    );
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Delete Project' })[1],
    );

    await waitFor(() => {
      expect(deleteProjectMock).toHaveBeenCalledWith('project-1');
    });
    expect(toastSuccessMock).toHaveBeenCalledWith({
      title: 'Project deleted',
      description: 'Your project has been deleted.',
    });
    expect(pushMock).toHaveBeenCalledWith('/profile');
  });

  test('shows an error toast when delete fails', async () => {
    deleteProjectMock.mockRejectedValue(new Error('Delete failed'));
    renderWithChakra(<EditProjectPage />);

    await screen.findByText('Delete project');
    fireEvent.click(screen.getByRole('button', { name: 'Delete Project' }));
    fireEvent.change(
      screen.getByLabelText('Type project title to confirm deletion'),
      { target: { value: 'demo project' } },
    );
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Delete Project' })[1],
    );

    await waitFor(() => {
      expect(toastErrorMock).toHaveBeenCalledWith({
        title: 'Could not delete project',
        description: 'Delete failed',
      });
    });
    expect(pushMock).not.toHaveBeenCalledWith('/profile');
  });
});
