import { apiUrl } from '@/lib/api/client';
import type {
  ProjectSearchParams,
  ProjectSearchResponse,
} from '@/lib/api/types/search';

function appendListParams(
  params: URLSearchParams,
  key: string,
  values?: string[],
) {
  if (!values || values.length === 0) return;
  for (const value of values) {
    const normalized = value.trim();
    if (!normalized) continue;
    params.append(key, normalized);
  }
}

function getErrorMessage(status: number, detail?: unknown): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (status === 400) return 'Invalid search request.';
  if (status === 422) return 'Search parameters are invalid.';
  if (status >= 500) return 'Search failed due to a server error.';
  return 'Search request failed.';
}

export async function searchProjects(
  request: ProjectSearchParams,
  accessToken?: string | null,
): Promise<ProjectSearchResponse> {
  const params = new URLSearchParams();

  if (request.q?.trim()) params.set('q', request.q.trim());
  if (request.limit) params.set('limit', String(request.limit));
  if (request.cursor) params.set('cursor', request.cursor);
  if (request.sort) params.set('sort', request.sort);
  if (request.published_from)
    params.set('published_from', request.published_from);
  if (request.published_to) params.set('published_to', request.published_to);

  appendListParams(params, 'categories', request.categories);
  appendListParams(params, 'tags', request.tags);
  appendListParams(params, 'tech_stack', request.tech_stack);

  const endpoint = apiUrl(`/api/v1/projects/search?${params.toString()}`);
  const headers: HeadersInit = accessToken
    ? { Authorization: `Bearer ${accessToken}` }
    : {};

  const res = await fetch(endpoint, {
    method: 'GET',
    headers,
    cache: 'no-store',
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      const payload = (await res.json()) as { detail?: unknown };
      detail = payload.detail;
    } catch {
      detail = undefined;
    }
    throw new Error(getErrorMessage(res.status, detail));
  }

  return (await res.json()) as ProjectSearchResponse;
}
