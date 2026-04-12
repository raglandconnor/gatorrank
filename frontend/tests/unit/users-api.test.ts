import { beforeEach, describe, expect, test, vi } from 'vitest';
import {
  getMe,
  getMyProjects,
  getUserProjectsByUsername,
  getUserPublic,
  patchMe,
} from '@/lib/api/users';

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

  test('getUserProjectsByUsername uses optional auth for public profile project access', async () => {
    await getUserProjectsByUsername('d_dovale');

    expect(requestJsonMock).toHaveBeenCalledWith(
      '/api/v1/users/by-username/d_dovale/projects?limit=20&sort=new',
      {
        auth: 'optional',
        fallbackErrorMessage: 'Failed to fetch projects',
      },
    );
  });

  test('getMyProjects keeps required auth for owner-only project access', async () => {
    await getMyProjects();

    expect(requestJsonMock).toHaveBeenCalledWith(
      '/api/v1/users/me/projects?limit=20&visibility=all&sort=new',
      {
        auth: 'required',
        fallbackErrorMessage: 'Failed to fetch your projects',
      },
    );
  });
});
