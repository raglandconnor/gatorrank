import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import { apiUrl } from '@/lib/api/client';
import type {
  ProjectListResponse,
  UserPrivate,
  UserPublic,
  UserUpdate,
} from '@/lib/api/types/user';

export async function getMe(): Promise<UserPrivate> {
  const res = await fetchWithAuth('/api/v1/users/me');
  if (!res.ok) {
    throw new Error('Failed to fetch profile');
  }
  return res.json() as Promise<UserPrivate>;
}

export async function patchMe(payload: UserUpdate): Promise<UserPrivate> {
  const res = await fetchWithAuth('/api/v1/users/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = 'Failed to update profile';
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data.detail === 'string') detail = data.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json() as Promise<UserPrivate>;
}

export async function getUserPublic(userId: string): Promise<UserPublic> {
  const res = await fetch(apiUrl(`/api/v1/users/${userId}`));
  if (res.status === 404) {
    const err = new Error('User not found') as Error & { status: number };
    err.status = 404;
    throw err;
  }
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json() as Promise<UserPublic>;
}

export async function getUserProjects(
  userId: string,
  limit = 20,
): Promise<ProjectListResponse> {
  const res = await fetchWithAuth(
    `/api/v1/users/${userId}/projects?limit=${limit}&sort=new`,
  );
  if (!res.ok) {
    throw new Error('Failed to fetch projects');
  }
  return res.json() as Promise<ProjectListResponse>;
}
