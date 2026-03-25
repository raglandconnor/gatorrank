export interface UserPrivate {
  id: string;
  email: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserUpdate {
  full_name?: string;
  profile_picture_url?: string | null;
}

export interface ProjectMemberInfo {
  user_id: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
}

export interface ProjectListItem {
  id: string;
  created_by_id: string;
  title: string;
  short_description: string;
  long_description: string | null;
  demo_url: string | null;
  github_url: string | null;
  video_url: string | null;
  vote_count: number;
  is_group_project: boolean;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  members: ProjectMemberInfo[];
}

export interface ProjectListResponse {
  items: ProjectListItem[];
  next_cursor: string | null;
}
