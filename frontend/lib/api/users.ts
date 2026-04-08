import { apiUrl } from '@/lib/api/client';
import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import {
  buildHttpError,
  buildQueryString,
  parseApiErrorMessage,
} from '@/lib/api/http';
import type {
  MyProjectsQuery,
  ProjectListQuery,
  ProjectListResponse,
} from '@/lib/api/types/project';
import type { UserPrivate, UserPublic, UserUpdate } from '@/lib/api/types/user';

async function parseUserResponse<T>(
  res: Response,
  fallback: string,
): Promise<T> {
  if (!res.ok) {
    const message = await parseApiErrorMessage(res, fallback);
    throw buildHttpError(message, res.status);
  }

  return res.json() as Promise<T>;
}

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
  const res = await fetchWithAuth('/api/v1/users/me');
  return parseUserResponse<UserPrivate>(res, 'Failed to fetch profile');
}

export async function patchMe(payload: UserUpdate): Promise<UserPrivate> {
  const res = await fetchWithAuth('/api/v1/users/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return parseUserResponse<UserPrivate>(res, 'Failed to update profile');
}

export async function getUserPublic(userId: string): Promise<UserPublic> {
  const res = await fetch(apiUrl(`/api/v1/users/${userId}`));
  return parseUserResponse<UserPublic>(res, 'Failed to fetch user profile');
}

export async function getUserPublicByUsername(
  username: string,
): Promise<UserPublic> {
  const res = await fetch(
    apiUrl(`/api/v1/users/by-username/${encodeURIComponent(username)}`),
  );
  return parseUserResponse<UserPublic>(res, 'Failed to fetch user profile');
}

export async function getUserProjects(
  userId: string,
  query: ProjectListQuery = { limit: 20, sort: 'new' },
): Promise<ProjectListResponse> {
  const res = await fetchWithAuth(
    `/api/v1/users/${userId}/projects${buildProjectsQuery(query)}`,
  );
  return parseUserResponse<ProjectListResponse>(
    res,
    'Failed to fetch projects',
  );
}

export async function getUserProjectsByUsername(
  username: string,
  query: ProjectListQuery = { limit: 20, sort: 'new' },
): Promise<ProjectListResponse> {
  const res = await fetchWithAuth(
    `/api/v1/users/by-username/${encodeURIComponent(username)}/projects${buildProjectsQuery(query)}`,
  );
  return parseUserResponse<ProjectListResponse>(
    res,
    'Failed to fetch projects',
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
  const res = await fetchWithAuth(`/api/v1/users/me/projects${qs}`);
  return parseUserResponse<ProjectListResponse>(
    res,
    'Failed to fetch your projects',
  );
}
