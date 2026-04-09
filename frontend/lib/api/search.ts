import { apiUrl } from '@/lib/api/client';
import { buildQueryString } from '@/lib/api/http';
import { requestJson } from '@/lib/api/request';
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

function buildSearchQuery(request: ProjectSearchParams): string {
  const qs = buildQueryString({
    q: request.q?.trim(),
    limit: request.limit,
    cursor: request.cursor,
    sort: request.sort,
    published_from: request.published_from,
    published_to: request.published_to,
  });

  if (
    !request.categories?.length &&
    !request.tags?.length &&
    !request.tech_stack?.length
  ) {
    return qs;
  }

  const params = new URLSearchParams(qs.replace(/^\?/, ''));
  appendListParams(params, 'categories', request.categories);
  appendListParams(params, 'tags', request.tags);
  appendListParams(params, 'tech_stack', request.tech_stack);
  const combined = params.toString();
  return combined ? `?${combined}` : '';
}

/**
 * Search projects through the backend query contract.
 *
 * If `accessToken` is provided, this uses refresh-aware auth request behavior.
 * If omitted, this performs anonymous search using plain fetch.
 */
export async function searchProjects(
  request: ProjectSearchParams,
  accessToken?: string | null,
): Promise<ProjectSearchResponse> {
  const query = buildSearchQuery(request);

  const path = `/api/v1/projects/search${query}`;
  if (accessToken == null) {
    return requestJson<ProjectSearchResponse>(apiUrl(path), {
      auth: 'none',
      method: 'GET',
      cache: 'no-store',
      fallbackErrorMessage: (res) =>
        res.status === 422
          ? 'Search parameters are invalid.'
          : 'Search request failed.',
    });
  }

  return requestJson<ProjectSearchResponse>(path, {
    auth: 'required',
    method: 'GET',
    cache: 'no-store',
    headers: { Authorization: `Bearer ${accessToken}` },
    fallbackErrorMessage: (res) =>
      res.status === 422
        ? 'Search parameters are invalid.'
        : 'Search request failed.',
  });
}
