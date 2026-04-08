import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import { buildHttpError, parseApiErrorMessage } from '@/lib/api/http';
import type { TaxonomyTerm } from '@/lib/api/types/project';

async function parseTaxonomyResponse<T>(
  res: Response,
  fallback: string,
): Promise<T> {
  if (!res.ok) {
    const message = await parseApiErrorMessage(res, fallback);
    throw buildHttpError(message, res.status);
  }

  return res.json() as Promise<T>;
}

export async function listTags(): Promise<TaxonomyTerm[]> {
  const res = await fetchWithAuth('/api/v1/taxonomy/tags');
  return parseTaxonomyResponse<TaxonomyTerm[]>(res, 'Failed to fetch tags');
}
