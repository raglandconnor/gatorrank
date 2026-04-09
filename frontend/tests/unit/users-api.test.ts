import { beforeEach, describe, expect, test, vi } from 'vitest';
import { getMe, getUserPublic, patchMe } from '@/lib/api/users';

const { requestJsonMock } = vi.hoisted(() => ({
  requestJsonMock: vi.fn(),
}));

vi.mock('@/lib/api/request', () => ({
  requestJson: requestJsonMock,
  requestVoid: vi.fn(),
}));

describe('users api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestJsonMock.mockResolvedValue({});
  });

  test('getMe uses required auth mode and profile fallback message', async () => {
    await getMe();

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/users/me', {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch profile',
    });
  });

  test('patchMe sends payload via required auth PATCH call', async () => {
    await patchMe({ full_name: 'New Name' });

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/users/me', {
      auth: 'required',
      method: 'PATCH',
      body: { full_name: 'New Name' },
      fallbackErrorMessage: 'Failed to update profile',
    });
  });

  test('getUserPublic uses anonymous mode for public profile access', async () => {
    await getUserPublic('user-123');

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/users/user-123', {
      auth: 'none',
      fallbackErrorMessage: 'Failed to fetch user profile',
    });
  });
});
