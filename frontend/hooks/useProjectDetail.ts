import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getProjectByIdForViewer } from '@/lib/api/projects';
import type { ProjectDetail } from '@/lib/api/types/project';

interface ProjectViewModel {
  id: string;
  name: string;
  shortDescription: string;
  fullDescription: string;
  imageUrl?: string;
  tags: string[];
  websiteUrl: string;
  githubUrl: string;
  demoVideoUrl: string;
  votes: number;
}

export function useProjectDetail(
  projectId: string,
  accessToken: string | null,
  isReady: boolean,
) {
  const [projectDetail, setProjectDetail] = useState<ProjectDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const requestIdRef = useRef(0);

  const loadProject = useCallback(async () => {
    if (!isReady) return;
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);
    setNotFound(false);

    try {
      const detail = await getProjectByIdForViewer(projectId, accessToken);
      if (requestId !== requestIdRef.current) return;
      setProjectDetail(detail);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      const status =
        typeof err === 'object' &&
        err !== null &&
        'status' in err &&
        typeof (err as { status?: unknown }).status === 'number'
          ? (err as { status: number }).status
          : null;
      if (status === 404) {
        setNotFound(true);
        setProjectDetail(null);
        return;
      }
      setError(
        err instanceof Error ? err.message : 'Failed to load project detail.',
      );
      setProjectDetail(null);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [accessToken, isReady, projectId]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const project = useMemo<ProjectViewModel | null>(() => {
    if (!projectDetail) return null;
    return {
      id: projectDetail.id,
      name: projectDetail.title,
      shortDescription: projectDetail.short_description,
      fullDescription:
        projectDetail.long_description ?? projectDetail.short_description,
      imageUrl: undefined,
      tags: (projectDetail.tags.length > 0
        ? projectDetail.tags
        : projectDetail.categories
      ).map((term) => term.name),
      websiteUrl: projectDetail.demo_url ?? '',
      githubUrl: projectDetail.github_url ?? '',
      demoVideoUrl: projectDetail.video_url ?? '',
      votes: projectDetail.vote_count,
    };
  }, [projectDetail]);

  const projectCreator = useMemo(() => {
    if (!projectDetail?.members.length) return null;
    return (
      projectDetail.members.find((member) => member.role === 'owner') ??
      projectDetail.members[0]
    );
  }, [projectDetail]);

  return {
    project,
    projectCreator,
    loading,
    error,
    notFound,
    loadProject,
  };
}
