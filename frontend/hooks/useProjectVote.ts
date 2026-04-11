'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { addProjectVote, removeProjectVote } from '@/lib/api/projects';
import { getStoredAccessToken } from '@/lib/auth/storage';
import { buildReturnToFromWindow } from '@/lib/auth/returnTo';
import { toast } from '@/lib/ui/toast';

interface UseProjectVoteOptions {
  projectId: string;
  initialVoteCount: number;
  initialViewerHasVoted: boolean;
}

interface HttpStatusError {
  status?: number;
}

function getStatus(error: unknown): number | null {
  if (typeof error !== 'object' || error === null) return null;
  const status = (error as HttpStatusError).status;
  return typeof status === 'number' ? status : null;
}

export function useProjectVote({
  projectId,
  initialVoteCount,
  initialViewerHasVoted,
}: UseProjectVoteOptions) {
  const router = useRouter();
  const [isVoted, setIsVoted] = useState(initialViewerHasVoted);
  const [voteCount, setVoteCount] = useState(initialVoteCount);
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    setIsVoted(initialViewerHasVoted);
    setVoteCount(initialVoteCount);
  }, [initialViewerHasVoted, initialVoteCount, projectId]);

  const redirectToLogin = useCallback(() => {
    const params = new URLSearchParams({
      returnTo: buildReturnToFromWindow(),
    });

    toast.info({
      title: 'Log in to vote',
      description:
        'Create your voice in project rankings, then vote instantly.',
    });

    router.push(`/login?${params.toString()}`);
  }, [router]);

  const toggleVote = useCallback(async () => {
    if (isPending) return;
    if (!projectId.trim()) return;

    if (!getStoredAccessToken()) {
      redirectToLogin();
      return;
    }

    const previousIsVoted = isVoted;
    const previousVoteCount = voteCount;
    const nextIsVoted = !previousIsVoted;

    setIsPending(true);
    setIsVoted(nextIsVoted);
    setVoteCount((prev) => Math.max(0, prev + (nextIsVoted ? 1 : -1)));

    try {
      if (nextIsVoted) {
        await addProjectVote(projectId);
      } else {
        await removeProjectVote(projectId);
      }
    } catch (error) {
      setIsVoted(previousIsVoted);
      setVoteCount(previousVoteCount);

      if (getStatus(error) === 401) {
        redirectToLogin();
        return;
      }

      toast.error({
        title: "Couldn't update vote",
        description: 'Please try again.',
      });
    } finally {
      setIsPending(false);
    }
  }, [isPending, isVoted, projectId, redirectToLogin, voteCount]);

  return {
    isVoted,
    voteCount,
    isPending,
    toggleVote,
  };
}
