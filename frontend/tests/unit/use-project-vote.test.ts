import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { useProjectVote } from '@/hooks/useProjectVote';

const {
  pushMock,
  addProjectVoteMock,
  removeProjectVoteMock,
  getStoredAccessTokenMock,
  toastInfoMock,
  toastErrorMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  addProjectVoteMock: vi.fn(),
  removeProjectVoteMock: vi.fn(),
  getStoredAccessTokenMock: vi.fn(),
  toastInfoMock: vi.fn(),
  toastErrorMock: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock('@/lib/api/projects', () => ({
  addProjectVote: addProjectVoteMock,
  removeProjectVote: removeProjectVoteMock,
}));

vi.mock('@/lib/auth/storage', () => ({
  getStoredAccessToken: getStoredAccessTokenMock,
}));

vi.mock('@/lib/ui/toast', () => ({
  toast: {
    info: toastInfoMock,
    error: toastErrorMock,
  },
}));

describe('useProjectVote', () => {
  beforeEach(() => {
    pushMock.mockReset();
    addProjectVoteMock.mockReset();
    removeProjectVoteMock.mockReset();
    getStoredAccessTokenMock.mockReset();
    toastInfoMock.mockReset();
    toastErrorMock.mockReset();
    getStoredAccessTokenMock.mockReturnValue('token');
    addProjectVoteMock.mockResolvedValue(undefined);
    removeProjectVoteMock.mockResolvedValue(undefined);
    window.history.replaceState({}, '', '/projects/p1?sort=top');
  });

  test('optimistically adds vote and persists on success', async () => {
    const { result } = renderHook(() =>
      useProjectVote({
        projectId: 'p1',
        initialVoteCount: 4,
        initialViewerHasVoted: false,
      }),
    );

    expect(result.current.voteCount).toBe(4);
    expect(result.current.isVoted).toBe(false);

    await act(async () => {
      await result.current.toggleVote();
    });

    expect(addProjectVoteMock).toHaveBeenCalledWith('p1');
    expect(removeProjectVoteMock).not.toHaveBeenCalled();
    expect(result.current.voteCount).toBe(5);
    expect(result.current.isVoted).toBe(true);
    expect(result.current.isPending).toBe(false);
  });

  test('rolls back optimistic vote when request fails', async () => {
    addProjectVoteMock.mockRejectedValueOnce(new Error('boom'));

    const { result } = renderHook(() =>
      useProjectVote({
        projectId: 'p1',
        initialVoteCount: 4,
        initialViewerHasVoted: false,
      }),
    );

    await act(async () => {
      await result.current.toggleVote();
    });

    expect(result.current.voteCount).toBe(4);
    expect(result.current.isVoted).toBe(false);
    expect(toastErrorMock).toHaveBeenCalledWith({
      title: "Couldn't update vote",
      description: 'Please try again.',
    });
  });

  test('redirects unauthenticated users to login and preserves return path', async () => {
    getStoredAccessTokenMock.mockReturnValueOnce(null);

    const { result } = renderHook(() =>
      useProjectVote({
        projectId: 'p1',
        initialVoteCount: 4,
        initialViewerHasVoted: false,
      }),
    );

    await act(async () => {
      await result.current.toggleVote();
    });

    expect(addProjectVoteMock).not.toHaveBeenCalled();
    expect(removeProjectVoteMock).not.toHaveBeenCalled();
    expect(toastInfoMock).toHaveBeenCalledWith({
      title: 'Log in to vote',
      description:
        'Create your voice in project rankings, then vote instantly.',
    });

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith(
        '/login?returnTo=%2Fprojects%2Fp1%3Fsort%3Dtop',
      );
    });
  });
});
