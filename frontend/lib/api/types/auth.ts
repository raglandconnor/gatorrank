/** Canonical authenticated user shape cached in frontend auth context. */

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
}
