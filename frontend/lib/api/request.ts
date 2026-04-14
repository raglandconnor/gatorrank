import { apiUrl } from '@/lib/api/client';
import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import {
  buildHttpError,
  buildQueryString,
  parseApiErrorMessage,
} from '@/lib/api/http';

/**
 * Shared frontend API request layer.
 *
 * Responsibilities:
 * - normalize URL, query, and request-init handling
 * - route requests by auth mode (none/required/optional)
 * - normalize backend errors into typed HttpError values
 *
 * Non-responsibilities:
 * - no UI-side effects such as navigation or toasts
 */
export type RequestAuthMode = 'none' | 'required' | 'optional';

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  /** `none`: anonymous fetch, `required`: refresh-aware auth, `optional`: auth only when token exists. */
  auth?: RequestAuthMode;
  headers?: HeadersInit;
  /** Plain objects are JSON-stringified; other BodyInit values are passed through. */
  body?: BodyInit | object | null;
  query?: Record<string, string | number | boolean | undefined>;
  /** Fallback when backend error payload lacks a usable `detail` message. */
  fallbackErrorMessage?: string | ((res: Response) => string);
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (value === null || typeof value !== 'object') return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function normalizeRequestInit(options: RequestOptions): RequestInit {
  const { body, headers, ...rest } = options;
  const normalizedHeaders = new Headers(headers);

  if (isPlainObject(body)) {
    if (!normalizedHeaders.has('Content-Type')) {
      normalizedHeaders.set('Content-Type', 'application/json');
    }

    return {
      ...rest,
      headers: normalizedHeaders,
      body: JSON.stringify(body),
    };
  }

  return {
    ...rest,
    headers: normalizedHeaders,
    body: body as BodyInit | null | undefined,
  };
}

function buildRequestPath(
  path: string,
  query?: Record<string, string | number | boolean | undefined>,
): string {
  const qs = query ? buildQueryString(query) : '';
  if (!qs) return path;

  const joiner = path.includes('?') ? '&' : '?';
  return `${path}${qs.replace(/^\?/, joiner)}`;
}

function toFetchUrl(pathWithQuery: string): string {
  if (
    pathWithQuery.startsWith('http://') ||
    pathWithQuery.startsWith('https://')
  ) {
    return pathWithQuery;
  }

  return apiUrl(
    pathWithQuery.startsWith('/') ? pathWithQuery : `/${pathWithQuery}`,
  );
}

async function executeRequest(
  path: string,
  options: RequestOptions = {},
): Promise<Response> {
  const { auth = 'none', query } = options;
  const init = normalizeRequestInit(options);
  const requestPath = buildRequestPath(path, query);

  if (auth === 'required') {
    return fetchWithAuth(requestPath, init);
  }

  if (auth === 'optional') {
    const authedRes = await fetchWithAuth(requestPath, init);
    if (authedRes.status !== 401) {
      return authedRes;
    }
    // Public/optional reads should stay resilient if local auth state is stale.
    return fetch(toFetchUrl(requestPath), init);
  }

  return fetch(toFetchUrl(requestPath), init);
}

async function ensureOkResponse(
  res: Response,
  fallbackErrorMessage?: string | ((res: Response) => string),
): Promise<Response> {
  if (res.ok) return res;

  const fallbackMessage =
    typeof fallbackErrorMessage === 'function'
      ? fallbackErrorMessage(res)
      : fallbackErrorMessage;

  const message = await parseApiErrorMessage(
    res,
    fallbackMessage ?? 'Request failed',
  );
  throw buildHttpError(message, res.status);
}

export async function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const res = await executeRequest(path, options);
  await ensureOkResponse(res, options.fallbackErrorMessage);

  if (res.status === 204) {
    throw new Error('Expected JSON response body but received 204 No Content');
  }

  return res.json() as Promise<T>;
}

/** Use for endpoints that are expected to return no response body (for example 204 routes). */
export async function requestVoid(
  path: string,
  options: RequestOptions = {},
): Promise<void> {
  const res = await executeRequest(path, options);
  await ensureOkResponse(res, options.fallbackErrorMessage);
}
