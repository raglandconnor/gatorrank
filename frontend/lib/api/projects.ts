import { apiUrl } from '@/lib/api/client';
import { buildQueryString } from '@/lib/api/http';
import { requestJson, requestVoid } from '@/lib/api/request';
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
  return requestJson<ProjectListResponse>(`/api/v1/projects${qs}`, {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch projects',
  });
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
  return requestJson<ProjectListResponse>(`/api/v1/projects${qs}`, {
    auth: 'none',
    method: 'GET',
    cache: 'no-store',
    fallbackErrorMessage: 'Failed to fetch projects',
  });
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(`/api/v1/projects/${projectId}`, {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch project',
  });
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
    return requestJson<ProjectDetail>(`/api/v1/projects/${projectId}`, {
      auth: 'none',
      method: 'GET',
      cache: 'no-store',
      fallbackErrorMessage: 'Failed to fetch project',
    });
  }
  return getProject(projectId);
}

export async function getProjectBySlug(slug: string): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(
    `/api/v1/projects/slug/${encodeURIComponent(slug)}`,
    {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch project',
    },
  );
}

export async function createProject(
  payload: ProjectCreateInput,
): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>('/api/v1/projects', {
    auth: 'required',
    method: 'POST',
    body: payload,
    fallbackErrorMessage: 'Failed to create project',
  });
}

export async function updateProject(
  projectId: string,
  payload: ProjectUpdateInput,
): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(`/api/v1/projects/${projectId}`, {
    auth: 'required',
    method: 'PATCH',
    body: payload,
    fallbackErrorMessage: 'Failed to update project',
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await requestVoid(`/api/v1/projects/${projectId}`, {
    auth: 'required',
    method: 'DELETE',
    fallbackErrorMessage: 'Failed to delete project',
  });
}

export async function publishProject(
  projectId: string,
): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(`/api/v1/projects/${projectId}/publish`, {
    auth: 'required',
    method: 'POST',
    fallbackErrorMessage: 'Failed to publish project',
  });
}

export async function unpublishProject(
  projectId: string,
): Promise<ProjectDetail> {
  return requestJson<ProjectDetail>(`/api/v1/projects/${projectId}/unpublish`, {
    auth: 'required',
    method: 'POST',
    fallbackErrorMessage: 'Failed to unpublish project',
  });
}

export async function listProjectMembers(
  projectId: string,
): Promise<ProjectMemberInfo[]> {
  return requestJson<ProjectMemberInfo[]>(
    `/api/v1/projects/${projectId}/members`,
    {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch project members',
    },
  );
}

export async function addProjectMember(
  projectId: string,
  payload: AddProjectMemberInput,
): Promise<ProjectMemberInfo> {
  return requestJson<ProjectMemberInfo>(
    `/api/v1/projects/${projectId}/members`,
    {
      auth: 'required',
      method: 'POST',
      body: payload,
      fallbackErrorMessage: 'Failed to add project member',
    },
  );
}

export async function updateProjectMember(
  projectId: string,
  userId: string,
  payload: UpdateProjectMemberInput,
): Promise<ProjectMemberInfo> {
  return requestJson<ProjectMemberInfo>(
    `/api/v1/projects/${projectId}/members/${userId}`,
    {
      auth: 'required',
      method: 'PATCH',
      body: payload,
      fallbackErrorMessage: 'Failed to update project member',
    },
  );
}

export async function removeProjectMember(
  projectId: string,
  userId: string,
): Promise<void> {
  await requestVoid(`/api/v1/projects/${projectId}/members/${userId}`, {
    auth: 'required',
    method: 'DELETE',
    fallbackErrorMessage: 'Failed to remove project member',
  });
}

export async function leaveProject(projectId: string): Promise<void> {
  await requestVoid(`/api/v1/projects/${projectId}/leave`, {
    auth: 'required',
    method: 'POST',
    fallbackErrorMessage: 'Failed to leave project',
  });
}

export async function addProjectVote(projectId: string): Promise<void> {
  await requestVoid(`/api/v1/projects/${projectId}/vote`, {
    auth: 'required',
    method: 'POST',
    fallbackErrorMessage: 'Failed to vote for project',
  });
}

export async function removeProjectVote(projectId: string): Promise<void> {
  await requestVoid(`/api/v1/projects/${projectId}/vote`, {
    auth: 'required',
    method: 'DELETE',
    fallbackErrorMessage: 'Failed to remove vote',
  });
}

export { apiUrl };
