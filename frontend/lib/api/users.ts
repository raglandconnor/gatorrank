import { buildQueryString } from '@/lib/api/http';
import { requestJson } from '@/lib/api/request';
import type {
  MyProjectsQuery,
  ProjectListQuery,
  ProjectListResponse,
} from '@/lib/api/types/project';
import type { UserPrivate, UserPublic, UserUpdate } from '@/lib/api/types/user';

function buildProjectsQuery(query: ProjectListQuery = {}): string {
  return buildQueryString({
    limit: query.limit,
    cursor: query.cursor,
    sort: query.sort,
    published_from: query.published_from,
    published_to: query.published_to,
  });
}

export async function getMe(): Promise<UserPrivate> {
  return requestJson<UserPrivate>('/api/v1/users/me', {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch profile',
  });
}

export async function patchMe(payload: UserUpdate): Promise<UserPrivate> {
  return requestJson<UserPrivate>('/api/v1/users/me', {
    auth: 'required',
    method: 'PATCH',
    body: payload,
    fallbackErrorMessage: 'Failed to update profile',
  });
}

export async function getUserPublic(userId: string): Promise<UserPublic> {
  return requestJson<UserPublic>(`/api/v1/users/${userId}`, {
    auth: 'none',
    fallbackErrorMessage: 'Failed to fetch user profile',
  });
}

export async function getUserPublicByUsername(
  username: string,
): Promise<UserPublic> {
  return requestJson<UserPublic>(
    `/api/v1/users/by-username/${encodeURIComponent(username)}`,
    {
      auth: 'none',
      fallbackErrorMessage: 'Failed to fetch user profile',
    },
  );
}

export async function getUserProjects(
  userId: string,
  query: ProjectListQuery = { limit: 20, sort: 'new' },
): Promise<ProjectListResponse> {
  return requestJson<ProjectListResponse>(
    `/api/v1/users/${userId}/projects${buildProjectsQuery(query)}`,
    {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch projects',
    },
  );
}

export async function getUserProjectsByUsername(
  username: string,
  query: ProjectListQuery = { limit: 20, sort: 'new' },
): Promise<ProjectListResponse> {
  return requestJson<ProjectListResponse>(
    `/api/v1/users/by-username/${encodeURIComponent(username)}/projects${buildProjectsQuery(query)}`,
    {
      auth: 'required',
      fallbackErrorMessage: 'Failed to fetch projects',
    },
  );
}

export async function getMyProjects(
  query: MyProjectsQuery = { limit: 20, sort: 'new', visibility: 'all' },
): Promise<ProjectListResponse> {
  const qs = buildQueryString({
    limit: query.limit,
    cursor: query.cursor,
    visibility: query.visibility,
    sort: query.sort,
    published_from: query.published_from,
    published_to: query.published_to,
  });
  return requestJson<ProjectListResponse>(`/api/v1/users/me/projects${qs}`, {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch your projects',
  });
}
