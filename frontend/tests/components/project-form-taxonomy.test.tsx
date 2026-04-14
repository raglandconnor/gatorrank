import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { ProjectForm } from '@/components/projects/ProjectForm';
import { renderWithChakra } from '@/tests/utils/render';

vi.mock('@/lib/api/taxonomy', () => ({
  listCategories: vi.fn().mockResolvedValue([]),
  listTags: vi.fn().mockResolvedValue([
    { id: 't1', name: 'React' },
    { id: 't2', name: 'ReasonML' },
    { id: 't3', name: 'TypeScript' },
  ]),
  listTechStacks: vi.fn().mockResolvedValue([]),
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  },
}));

function renderProjectForm() {
  return renderWithChakra(
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
      members={[]}
      pendingMembers={[]}
      onAddMember={vi.fn().mockResolvedValue({ ok: true })}
      onRemoveMember={vi.fn().mockResolvedValue({ ok: true })}
    />,
  );
}

describe('ProjectForm taxonomy fields', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('pressing Enter selects the first matching suggestion', async () => {
    renderProjectForm();

    const tagInput = await screen.findByPlaceholderText('Start typing a tag');
    fireEvent.focus(tagInput);
    fireEvent.change(tagInput, { target: { value: 'rea' } });

    expect(
      await screen.findByText('Press Enter to use "React".'),
    ).toBeInTheDocument();

    fireEvent.keyDown(tagInput, { key: 'Enter' });

    expect(await screen.findByLabelText('Remove React')).toBeInTheDocument();
  });

  test('shows explicit create action and allows adding a custom term', async () => {
    renderProjectForm();

    const tagInput = await screen.findByPlaceholderText('Start typing a tag');
    fireEvent.focus(tagInput);
    fireEvent.change(tagInput, { target: { value: 'React Native' } });

    const createButton = await screen.findByRole('button', {
      name: 'Create "React Native"',
    });
    fireEvent.click(createButton);

    expect(
      await screen.findByLabelText('Remove React Native'),
    ).toBeInTheDocument();
  });
});
