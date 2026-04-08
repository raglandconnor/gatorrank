/** Mirrors backend AuthUserResponse / AuthMeResponse public fields used on the client. */

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  role: string;
  full_name: string | null;
  profile_picture_url: string | null;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
  refresh_token_expires_in: number;
  user: AuthUser;
}

export interface AuthMeResponse extends AuthUser {
  created_at: string;
  updated_at: string;
}

export interface AuthSignupBody {
  email: string;
  password: string;
  username: string;
  full_name?: string | null;
  remember_me?: boolean;
}

export interface AuthLoginBody {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface AuthRefreshBody {
  refresh_token: string;
}

export interface AuthLogoutBody {
  refresh_token: string;
}
