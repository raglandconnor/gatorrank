import type { ProjectListItem } from '@/lib/api/types/project';

export type SearchSort = 'top' | 'new';

export type SearchProjectListItem = ProjectListItem;

export interface ProjectSearchResponse {
  items: SearchProjectListItem[];
  next_cursor: string | null;
}

export interface ProjectSearchParams {
  q?: string;
  categories?: string[];
  tags?: string[];
  tech_stack?: string[];
  limit?: number;
  cursor?: string;
  sort?: SearchSort;
  published_from?: string;
  published_to?: string;
}
