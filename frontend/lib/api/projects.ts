import { apiUrl } from '@/lib/api/client';
import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import {
  buildHttpError,
  buildQueryString,
  parseApiErrorMessage,
} from '@/lib/api/http';
import type {
  AddProjectMemberInput,
  ProjectCreateInput,
  ProjectDetail,
  ProjectListQuery,
  ProjectListResponse,
  ProjectMemberInfo,
  ProjectUpdateInput,
  UpdateProjectMemberInput,
} from '@/lib/api/types/project';

async function parseProjectResponse<T>(
  res: Response,
  fallback: string,
): Promise<T> {
  if (!res.ok) {
    const message = await parseApiErrorMessage(res, fallback);
    throw buildHttpError(message, res.status);
  }

  return res.json() as Promise<T>;
}

export async function listProjects(
  query: ProjectListQuery = {},
): Promise<ProjectListResponse> {
  const qs = buildQueryString({
    limit: query.limit,
    cursor: query.cursor,
    sort: query.sort,
    published_from: query.published_from,
    published_to: query.published_to,
  });
  const res = await fetchWithAuth(`/api/v1/projects${qs}`);
  return parseProjectResponse<ProjectListResponse>(
    res,
    'Failed to fetch projects',
  );
}

/**
 * Public-safe project listing for unauthenticated pages (e.g. Home/Top Projects).
 * Does not trigger auth refresh/redirect behavior.
 */
export async function listProjectsPublic(
  query: ProjectListQuery = {},
): Promise<ProjectListResponse> {
  const qs = buildQueryString({
    limit: query.limit,
    cursor: query.cursor,
    sort: query.sort,
    published_from: query.published_from,
    published_to: query.published_to,
  });
  const res = await fetch(apiUrl(`/api/v1/projects${qs}`), {
    method: 'GET',
    cache: 'no-store',
  });
  return parseProjectResponse<ProjectListResponse>(
    res,
    'Failed to fetch projects',
  );
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}`);
  return parseProjectResponse<ProjectDetail>(res, 'Failed to fetch project');
}

export async function getProjectById(
  projectId: string,
): Promise<ProjectDetail> {
  return getProject(projectId);
}

/**
 * Fetch project detail with optional viewer context.
 *
 * Anonymous requests use plain fetch so public detail pages remain accessible
 * without auth state. Authenticated requests use refresh-aware fetch behavior.
 */
export async function getProjectByIdForViewer(
  projectId: string,
  accessToken?: string | null,
): Promise<ProjectDetail> {
  if (!accessToken) {
    const res = await fetch(apiUrl(`/api/v1/projects/${projectId}`), {
      method: 'GET',
      cache: 'no-store',
    });
    return parseProjectResponse<ProjectDetail>(res, 'Failed to fetch project');
  }
  return getProject(projectId);
}

export async function getProjectBySlug(slug: string): Promise<ProjectDetail> {
  const res = await fetchWithAuth(
    `/api/v1/projects/slug/${encodeURIComponent(slug)}`,
  );
  return parseProjectResponse<ProjectDetail>(res, 'Failed to fetch project');
}

export async function createProject(
  payload: ProjectCreateInput,
): Promise<ProjectDetail> {
  const res = await fetchWithAuth('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return parseProjectResponse<ProjectDetail>(res, 'Failed to create project');
}

export async function updateProject(
  projectId: string,
  payload: ProjectUpdateInput,
): Promise<ProjectDetail> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return parseProjectResponse<ProjectDetail>(res, 'Failed to update project');
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}`, {
    method: 'DELETE',
  });

  if (!res.ok && res.status !== 204) {
    const message = await parseApiErrorMessage(res, 'Failed to delete project');
    throw buildHttpError(message, res.status);
  }
}

export async function publishProject(
  projectId: string,
): Promise<ProjectDetail> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/publish`, {
    method: 'POST',
  });
  return parseProjectResponse<ProjectDetail>(res, 'Failed to publish project');
}

export async function unpublishProject(
  projectId: string,
): Promise<ProjectDetail> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/unpublish`, {
    method: 'POST',
  });
  return parseProjectResponse<ProjectDetail>(
    res,
    'Failed to unpublish project',
  );
}

export async function listProjectMembers(
  projectId: string,
): Promise<ProjectMemberInfo[]> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/members`);
  return parseProjectResponse<ProjectMemberInfo[]>(
    res,
    'Failed to fetch project members',
  );
}

export async function addProjectMember(
  projectId: string,
  payload: AddProjectMemberInput,
): Promise<ProjectMemberInfo> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return parseProjectResponse<ProjectMemberInfo>(
    res,
    'Failed to add project member',
  );
}

export async function updateProjectMember(
  projectId: string,
  userId: string,
  payload: UpdateProjectMemberInput,
): Promise<ProjectMemberInfo> {
  const res = await fetchWithAuth(
    `/api/v1/projects/${projectId}/members/${userId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
  );
  return parseProjectResponse<ProjectMemberInfo>(
    res,
    'Failed to update project member',
  );
}

export async function removeProjectMember(
  projectId: string,
  userId: string,
): Promise<void> {
  const res = await fetchWithAuth(
    `/api/v1/projects/${projectId}/members/${userId}`,
    {
      method: 'DELETE',
    },
  );

  if (!res.ok && res.status !== 204) {
    const message = await parseApiErrorMessage(
      res,
      'Failed to remove project member',
    );
    throw buildHttpError(message, res.status);
  }
}

export async function leaveProject(projectId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/leave`, {
    method: 'POST',
  });

  if (!res.ok && res.status !== 204) {
    const message = await parseApiErrorMessage(res, 'Failed to leave project');
    throw buildHttpError(message, res.status);
  }
}

export async function addProjectVote(projectId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/vote`, {
    method: 'POST',
  });

  if (!res.ok && res.status !== 204) {
    const message = await parseApiErrorMessage(
      res,
      'Failed to vote for project',
    );
    throw buildHttpError(message, res.status);
  }
}

export async function removeProjectVote(projectId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/projects/${projectId}/vote`, {
    method: 'DELETE',
  });

  if (!res.ok && res.status !== 204) {
    const message = await parseApiErrorMessage(res, 'Failed to remove vote');
    throw buildHttpError(message, res.status);
  }
}

export { apiUrl };
