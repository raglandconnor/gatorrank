import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import {
  authLogin,
  authLogout,
  authMe,
  authRefresh,
  authSignup,
} from '@/lib/api/auth';

const { requestJsonMock, requestVoidMock } = vi.hoisted(() => ({
  requestJsonMock: vi.fn(),
  requestVoidMock: vi.fn(),
}));

vi.mock('@/lib/api/request', () => ({
  requestJson: requestJsonMock,
  requestVoid: requestVoidMock,
}));

describe('auth api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    requestJsonMock.mockReset();
    requestVoidMock.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('authSignup uses requestJson with anonymous POST body', async () => {
    requestJsonMock.mockResolvedValue({ access_token: 'a' });

    await authSignup({
      email: 'user@example.com',
      username: 'gator',
      password: 'averysecurepassword',
      remember_me: true,
    });

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/auth/signup', {
      auth: 'none',
      method: 'POST',
      body: {
        email: 'user@example.com',
        username: 'gator',
        password: 'averysecurepassword',
        remember_me: true,
      },
    });
  });

  test('authLogin uses requestJson with anonymous POST body', async () => {
    requestJsonMock.mockResolvedValue({ access_token: 'a' });

    await authLogin({
      email: 'user@example.com',
      password: 'averysecurepassword',
      remember_me: false,
    });

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/auth/login', {
      auth: 'none',
      method: 'POST',
      body: {
        email: 'user@example.com',
        password: 'averysecurepassword',
        remember_me: false,
      },
    });
  });

  test('authMe preserves explicit bearer header behavior', async () => {
    requestJsonMock.mockResolvedValue({ id: 'u1' });

    await authMe('token-123');

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/auth/me', {
      auth: 'none',
      method: 'GET',
      headers: {
        Authorization: 'Bearer token-123',
      },
    });
  });

  test('authRefresh uses requestJson with refresh payload', async () => {
    requestJsonMock.mockResolvedValue({ access_token: 'next' });

    await authRefresh({ refresh_token: 'refresh-1' });

    expect(requestJsonMock).toHaveBeenCalledWith('/api/v1/auth/refresh', {
      auth: 'none',
      method: 'POST',
      body: { refresh_token: 'refresh-1' },
    });
  });

  test('authLogout uses requestVoid and supports 204 contract', async () => {
    requestVoidMock.mockResolvedValue(undefined);

    await authLogout({ refresh_token: 'refresh-1' });

    expect(requestVoidMock).toHaveBeenCalledWith('/api/v1/auth/logout', {
      auth: 'none',
      method: 'POST',
      body: { refresh_token: 'refresh-1' },
    });
  });

  test('propagates typed HttpError from shared request layer', async () => {
    const err = Object.assign(new Error('Invalid credentials'), {
      status: 401,
    });
    requestJsonMock.mockRejectedValue(err);

    await expect(
      authLogin({
        email: 'user@example.com',
        password: 'wrong-password',
      }),
    ).rejects.toMatchObject({
      message: 'Invalid credentials',
      status: 401,
    });
  });
});
