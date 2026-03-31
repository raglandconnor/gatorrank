/**
 * Base URL for the FastAPI backend (e.g. http://localhost:8000).
 * Must be set in .env as NEXT_PUBLIC_API_BASE_URL for browser fetches.
 */
export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ?? '';
  if (!base) {
    throw new Error(
      'NEXT_PUBLIC_API_BASE_URL is not set. Add it to frontend/.env (see .env.example).',
    );
  }
  return base;
}

export function apiUrl(path: string): string {
  const base = getApiBaseUrl();
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}
