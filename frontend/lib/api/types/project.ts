export type ProjectSort = 'top' | 'new';
export type MyProjectsVisibility = 'all' | 'published' | 'draft';
export type ProjectMemberRole = 'owner' | 'maintainer' | 'contributor';
export type ProjectMemberWritableRole = 'maintainer' | 'contributor';

export interface TaxonomyTerm {
  id: string;
  name: string;
}

export interface ProjectMemberInfo {
  user_id: string;
  username: string;
  role: ProjectMemberRole;
  full_name: string | null;
  profile_picture_url: string | null;
}

export interface ProjectBase {
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
  categories: TaxonomyTerm[];
  tags: TaxonomyTerm[];
  tech_stack: TaxonomyTerm[];
}

export interface ProjectListItem extends ProjectBase {
  members: ProjectMemberInfo[];
}

export interface ProjectDetail extends ProjectBase {
  members: ProjectMemberInfo[];
}

export interface ProjectListResponse {
  items: ProjectListItem[];
  next_cursor: string | null;
}

export interface ProjectListQuery {
  limit?: number;
  cursor?: string;
  sort?: ProjectSort;
  published_from?: string;
  published_to?: string;
}

export interface MyProjectsQuery extends ProjectListQuery {
  visibility?: MyProjectsVisibility;
}

export interface ProjectCreateInput {
  title: string;
  short_description: string;
  long_description?: string | null;
  demo_url?: string | null;
  github_url?: string | null;
  video_url?: string | null;
  timeline_start_date?: string | null;
  timeline_end_date?: string | null;
  categories?: string[];
  tags?: string[];
  tech_stack?: string[];
}

export interface ProjectUpdateInput {
  title?: string;
  short_description?: string;
  long_description?: string | null;
  demo_url?: string | null;
  github_url?: string | null;
  video_url?: string | null;
  timeline_start_date?: string | null;
  timeline_end_date?: string | null;
  categories?: string[];
  tags?: string[];
  tech_stack?: string[];
}

export interface AddProjectMemberInput {
  email: string;
  role?: ProjectMemberWritableRole;
}

export interface UpdateProjectMemberInput {
  role: ProjectMemberWritableRole;
}
