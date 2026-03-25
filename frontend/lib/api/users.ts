import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import type {
  ProjectListResponse,
  UserPrivate,
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
