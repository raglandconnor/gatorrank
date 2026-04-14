import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { SignupFormPanel } from '@/components/auth/SignupFormPanel';
import { renderWithChakra } from '@/tests/utils/render';

const { pushMock, signupMock, toastSuccessMock, toastErrorMock } = vi.hoisted(
  () => ({
    pushMock: vi.fn(),
    signupMock: vi.fn(),
    toastSuccessMock: vi.fn(),
    toastErrorMock: vi.fn(),
  }),
);

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock('@/components/domain/AuthProvider', () => ({
  useAuth: () => ({
    signup: signupMock,
    isReady: true,
  }),
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  },
}));

describe('SignupFormPanel', () => {
  beforeEach(() => {
    pushMock.mockReset();
    signupMock.mockReset();
    toastSuccessMock.mockReset();
    toastErrorMock.mockReset();
    signupMock.mockResolvedValue(undefined);
  });

  test('submits signup and routes to check-email screen', async () => {
    renderWithChakra(<SignupFormPanel />);

    fireEvent.change(screen.getByLabelText('Full Name'), {
      target: { value: 'Connor Ragland' },
    });
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'raglandconnor' },
    });
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'raglandconnor@ufl.edu' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'supersecurepassword123' },
    });
    fireEvent.change(screen.getByLabelText('Confirm Password'), {
      target: { value: 'supersecurepassword123' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Sign Up' }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        email: 'raglandconnor@ufl.edu',
        username: 'raglandconnor',
        password: 'supersecurepassword123',
        fullName: 'Connor Ragland',
        rememberMe: false,
      });
    });

    expect(toastSuccessMock).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith(
      '/signup/check-email?email=raglandconnor%40ufl.edu',
    );
  });
});
