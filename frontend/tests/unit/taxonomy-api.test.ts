import { beforeEach, describe, expect, test, vi } from 'vitest';
import { listCategories, listTags, listTechStacks } from '@/lib/api/taxonomy';

const { requestJsonMock } = vi.hoisted(() => ({
  requestJsonMock: vi.fn(),
}));

vi.mock('@/lib/api/request', () => ({
  requestJson: requestJsonMock,
}));

describe('taxonomy api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestJsonMock.mockResolvedValue([]);
  });

  test('listCategories uses required auth mode and fallback message', async () => {
    await listCategories();

    expect(requestJsonMock).toHaveBeenCalledWith(
      '/api/v1/taxonomy/categories',
      {
        auth: 'required',
        fallbackErrorMessage: 'Failed to fetch categories',
      },
    );
  });

  test('listTags uses required auth mode and fallback message', async () => {
    await listTags();

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/taxonomy/tags', {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch tags',
    });
  });

  test('listTechStacks uses required auth mode and fallback message', async () => {
    await listTechStacks();

    expect(requestJsonMock).toHaveBeenCalledWith(
      '/api/v1/taxonomy/tech-stacks',
      {
        auth: 'required',
        fallbackErrorMessage: 'Failed to fetch tech stack terms',
      },
    );
  });
});
