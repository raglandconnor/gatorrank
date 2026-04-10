import { requestJson } from '@/lib/api/request';
import type { TaxonomyTerm } from '@/lib/api/types/project';

export async function listTags(): Promise<TaxonomyTerm[]> {
  return requestJson<TaxonomyTerm[]>('/api/v1/taxonomy/tags', {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch tags',
  });
}
