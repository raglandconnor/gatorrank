import { apiUrl } from '@/lib/api/client';
import { getSupabaseBrowserClient } from '@/lib/supabase/browser';

export interface FetchWithAuthOptions extends Omit<RequestInit, 'headers'> {
  headers?: HeadersInit;
}

async function getAccessToken(): Promise<string | null> {
  const supabase = getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.getSession();
  if (error) {
    return null;
  }
  return data.session?.access_token ?? null;
}

/**
 * GET/POST/etc. to `/api/v1/...` with Bearer access token from Supabase session.
 *
 * This helper is transport-only and intentionally does not perform navigation.
 * Route redirects/login UX are handled by higher-level auth/UI layers.
 */
export async function fetchWithAuth(
  path: string,
  init: FetchWithAuthOptions = {},
): Promise<Response> {
  const url = path.startsWith('http')
    ? path
    : apiUrl(path.startsWith('/') ? path : `/${path}`);

  const doFetch = (accessToken: string | null) => {
    const headers = new Headers(init.headers);
    if (typeof init.body === 'string' && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }
    return fetch(url, { ...init, headers });
  };

  const access = await getAccessToken();
  return doFetch(access);
}
