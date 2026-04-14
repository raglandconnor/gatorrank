import { requestJson } from '@/lib/api/request';
import type { TaxonomyTerm } from '@/lib/api/types/project';

export async function listCategories(): Promise<TaxonomyTerm[]> {
  return requestJson<TaxonomyTerm[]>('/api/v1/taxonomy/categories', {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch categories',
  });
}

export async function listTags(): Promise<TaxonomyTerm[]> {
  return requestJson<TaxonomyTerm[]>('/api/v1/taxonomy/tags', {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch tags',
  });
}

export async function listTechStacks(): Promise<TaxonomyTerm[]> {
  return requestJson<TaxonomyTerm[]>('/api/v1/taxonomy/tech-stacks', {
    auth: 'required',
    fallbackErrorMessage: 'Failed to fetch tech stack terms',
  });
}
