import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { renderWithChakra } from '@/tests/utils/render';
import { LoginFormPanel } from '@/components/auth/LoginFormPanel';

const { pushMock, loginMock, toastSuccessMock, toastErrorMock } = vi.hoisted(
  () => ({
    pushMock: vi.fn(),
    loginMock: vi.fn(),
    toastSuccessMock: vi.fn(),
    toastErrorMock: vi.fn(),
  }),
);

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock('@/components/domain/AuthProvider', () => ({
  useAuth: () => ({
    login: loginMock,
    isReady: true,
  }),
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  },
}));

describe('LoginFormPanel returnTo behavior', () => {
  beforeEach(() => {
    pushMock.mockReset();
    loginMock.mockReset();
    toastSuccessMock.mockReset();
    toastErrorMock.mockReset();
    loginMock.mockResolvedValue(undefined);
  });

  async function submitValidLogin() {
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'student@ufl.edu' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'valid-password-123' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith(
        'student@ufl.edu',
        'valid-password-123',
        false,
      );
    });
  }

  test('routes to a valid in-app returnTo after successful login', async () => {
    renderWithChakra(<LoginFormPanel returnTo="/projects/search?q=ai" />);

    await submitValidLogin();

    expect(pushMock).toHaveBeenCalledWith('/projects/search?q=ai');
    expect(toastSuccessMock).toHaveBeenCalled();
  });

  test('falls back to /profile for invalid external returnTo values', async () => {
    renderWithChakra(<LoginFormPanel returnTo="https://evil.example/phish" />);

    await submitValidLogin();

    expect(pushMock).toHaveBeenCalledWith('/profile');
    expect(toastSuccessMock).toHaveBeenCalled();
  });
});
