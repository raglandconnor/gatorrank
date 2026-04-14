import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  PendingProjectMember,
  ProjectForm,
} from '@/components/projects/ProjectForm';
import type { ProjectMemberInfo } from '@/lib/api/types/project';
import { toast } from '@/lib/ui/toast';
import { renderWithChakra } from '@/tests/utils/render';

vi.mock('@/lib/api/taxonomy', () => ({
  listCategories: vi.fn().mockResolvedValue([]),
  listTags: vi.fn().mockResolvedValue([]),
  listTechStacks: vi.fn().mockResolvedValue([]),
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}));

const baseMembers: ProjectMemberInfo[] = [
  {
    user_id: 'owner-1',
    username: 'owner',
    role: 'owner',
    full_name: 'Owner User',
    profile_picture_url: null,
  },
  {
    user_id: 'member-1',
    username: 'member',
    role: 'contributor',
    full_name: 'Member User',
    profile_picture_url: null,
  },
];

const basePendingMembers: PendingProjectMember[] = [
  { email: 'pending@ufl.edu', role: 'contributor' },
];

describe('ProjectForm member roles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('shows owner role as read-only text', () => {
    renderWithChakra(
      <ProjectForm
        mode="edit"
        initialValues={{
          title: 'Project One',
          shortDescription: 'Summary',
          fullDescription: '',
          imageUrl: null,
          categories: [],
          tags: [],
          techStack: [],
          websiteUrl: 'https://example.com',
          githubUrl: '',
          demoVideoUrl: '',
        }}
        onSubmit={vi.fn()}
        publishChecked
        onPublishCheckedChange={vi.fn()}
        members={baseMembers}
        pendingMembers={basePendingMembers}
        onAddMember={vi.fn().mockResolvedValue({ ok: true })}
        onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
      />,
    );

    expect(screen.getByText('owner')).toBeInTheDocument();
    expect(screen.getByLabelText('Role for Member User')).toBeInTheDocument();
  });

  test('calls onUpdateMemberRole when non-owner role select changes', async () => {
    const onUpdateMemberRole = vi.fn().mockResolvedValue({ ok: true });

    renderWithChakra(
      <ProjectForm
        mode="edit"
        initialValues={{
          title: 'Project One',
          shortDescription: 'Summary',
          fullDescription: '',
          imageUrl: null,
          categories: [],
          tags: [],
          techStack: [],
          websiteUrl: 'https://example.com',
          githubUrl: '',
          demoVideoUrl: '',
        }}
        onSubmit={vi.fn()}
        publishChecked
        onPublishCheckedChange={vi.fn()}
        members={baseMembers}
        pendingMembers={basePendingMembers}
        onAddMember={vi.fn().mockResolvedValue({ ok: true })}
        onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
        onUpdateMemberRole={onUpdateMemberRole}
      />,
    );

    fireEvent.change(screen.getByLabelText('Role for Member User'), {
      target: { value: 'maintainer' },
    });

    expect(onUpdateMemberRole).toHaveBeenCalledWith('member-1', 'maintainer');
  });

  test('calls onUpdatePendingMemberRole when pending member role changes', () => {
    const onUpdatePendingMemberRole = vi.fn();

    renderWithChakra(
      <ProjectForm
        mode="create"
        initialValues={{
          title: 'Project One',
          shortDescription: 'Summary',
          fullDescription: '',
          imageUrl: null,
          categories: [],
          tags: [],
          techStack: [],
          websiteUrl: 'https://example.com',
          githubUrl: '',
          demoVideoUrl: '',
        }}
        onSubmit={vi.fn()}
        publishChecked
        onPublishCheckedChange={vi.fn()}
        members={baseMembers}
        pendingMembers={basePendingMembers}
        onAddMember={vi.fn().mockResolvedValue({ ok: true })}
        onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
        onUpdatePendingMemberRole={onUpdatePendingMemberRole}
      />,
    );

    fireEvent.change(screen.getByLabelText('Role for pending@ufl.edu'), {
      target: { value: 'maintainer' },
    });

    expect(onUpdatePendingMemberRole).toHaveBeenCalledWith(
      'pending@ufl.edu',
      'maintainer',
    );
  });

  test('accepts non-ufl valid emails when adding pending members', async () => {
    const onAddMember = vi.fn().mockResolvedValue({ ok: true });

    renderWithChakra(
      <ProjectForm
        mode="create"
        initialValues={{
          title: 'Project One',
          shortDescription: 'Summary',
          fullDescription: '',
          imageUrl: null,
          categories: [],
          tags: [],
          techStack: [],
          websiteUrl: 'https://example.com',
          githubUrl: '',
          demoVideoUrl: '',
        }}
        onSubmit={vi.fn()}
        publishChecked
        onPublishCheckedChange={vi.fn()}
        members={baseMembers}
        pendingMembers={basePendingMembers}
        onAddMember={onAddMember}
        onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText('name@example.com'), {
      target: { value: 'teammate@gmail.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add team member' }));

    await waitFor(() => {
      expect(onAddMember).toHaveBeenCalledWith(
        'teammate@gmail.com',
        'contributor',
      );
    });
  });

  test('rejects malformed member emails before calling add callback', () => {
    const onAddMember = vi.fn().mockResolvedValue({ ok: true });

    renderWithChakra(
      <ProjectForm
        mode="create"
        initialValues={{
          title: 'Project One',
          shortDescription: 'Summary',
          fullDescription: '',
          imageUrl: null,
          categories: [],
          tags: [],
          techStack: [],
          websiteUrl: 'https://example.com',
          githubUrl: '',
          demoVideoUrl: '',
        }}
        onSubmit={vi.fn()}
        publishChecked
        onPublishCheckedChange={vi.fn()}
        members={baseMembers}
        pendingMembers={basePendingMembers}
        onAddMember={onAddMember}
        onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText('name@example.com'), {
      target: { value: 'not-an-email' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add team member' }));

    expect(onAddMember).not.toHaveBeenCalled();
    expect(toast.error).toHaveBeenCalledWith({
      title: 'Invalid email',
      description: 'Please enter a valid email address.',
    });
  });
});
