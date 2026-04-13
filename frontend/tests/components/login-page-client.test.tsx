import { renderWithChakra } from '@/tests/utils/render';
import { waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { LoginPageClient } from '@/components/auth/LoginPageClient';

const { replaceMock, toastSuccessMock, loginPanelMock, loginPanelPropsRef } =
  vi.hoisted(() => ({
    replaceMock: vi.fn(),
    toastSuccessMock: vi.fn(),
    loginPanelMock: vi.fn(() => <div data-testid="login-panel" />),
    loginPanelPropsRef: { value: null as { returnTo?: string | null } | null },
  }));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    success: toastSuccessMock,
  },
}));

vi.mock('@/components/auth/LoginFormPanel', () => ({
  LoginFormPanel: ({ returnTo }: { returnTo?: string | null }) => {
    loginPanelPropsRef.value = { returnTo };
    return loginPanelMock();
  },
}));

describe('LoginPageClient', () => {
  beforeEach(() => {
    replaceMock.mockReset();
    toastSuccessMock.mockReset();
    loginPanelMock.mockReset();
    loginPanelPropsRef.value = null;
  });

  test('shows signed-out toast once and normalizes URL to /login', async () => {
    renderWithChakra(<LoginPageClient signedOut returnTo={null} />);

    await waitFor(() => {
      expect(toastSuccessMock).toHaveBeenCalledWith({
        title: 'Signed out',
        description: 'You have been successfully signed out.',
      });
      expect(replaceMock).toHaveBeenCalledWith('/login');
    });
  });

  test('does not show toast or replace URL when signedOut is false', async () => {
    renderWithChakra(<LoginPageClient signedOut={false} returnTo={null} />);

    await waitFor(() => {
      expect(loginPanelMock).toHaveBeenCalled();
    });
    expect(toastSuccessMock).not.toHaveBeenCalled();
    expect(replaceMock).not.toHaveBeenCalled();
  });

  test('passes returnTo down to LoginFormPanel', async () => {
    renderWithChakra(
      <LoginPageClient signedOut={false} returnTo="/projects/search?q=ai" />,
    );

    await waitFor(() => {
      expect(loginPanelPropsRef.value).toEqual({
        returnTo: '/projects/search?q=ai',
      });
    });
  });
});
