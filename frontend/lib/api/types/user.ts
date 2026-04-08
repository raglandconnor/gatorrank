export interface UserPublic {
  id: string;
  username: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
  created_at: string;
}

export interface UserPrivate {
  id: string;
  email: string;
  username: string;
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
