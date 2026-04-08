export type SearchSort = 'top' | 'new';

export interface TaxonomyTermResponse {
  id: string;
  name: string;
}

export interface ProjectMemberInfo {
  user_id: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
}

export interface SearchProjectListItem {
  id: string;
  created_by_id: string;
  title: string;
  slug: string;
  short_description: string;
  long_description: string | null;
  demo_url: string | null;
  github_url: string | null;
  video_url: string | null;
  timeline_start_date: string | null;
  timeline_end_date: string | null;
  vote_count: number;
  team_size: number;
  is_group_project: boolean;
  is_published: boolean;
  viewer_has_voted: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  categories: TaxonomyTermResponse[];
  tags: TaxonomyTermResponse[];
  tech_stack: TaxonomyTermResponse[];
  members: ProjectMemberInfo[];
}

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
