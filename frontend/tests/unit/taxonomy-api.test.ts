import { beforeEach, describe, expect, test, vi } from 'vitest';
import { listTags } from '@/lib/api/taxonomy';

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

  test('listTags uses required auth mode and fallback message', async () => {
    await listTags();

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/taxonomy/tags', {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch tags',
    });
  });
});
