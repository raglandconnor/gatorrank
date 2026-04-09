import { apiUrl } from '@/lib/api/client';
import { fetchWithAuth } from '@/lib/api/fetchWithAuth';
import { getStoredAccessToken } from '@/lib/auth/storage';
import {
  buildHttpError,
  buildQueryString,
  parseApiErrorMessage,
} from '@/lib/api/http';

export type RequestAuthMode = 'none' | 'required' | 'optional';

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  auth?: RequestAuthMode;
  headers?: HeadersInit;
  body?: BodyInit | object | null;
  query?: Record<string, string | number | boolean | undefined>;
  fallbackErrorMessage?: string;
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

  if (auth === 'optional' && getStoredAccessToken()) {
    return fetchWithAuth(requestPath, init);
  }

  return fetch(toFetchUrl(requestPath), init);
}

async function ensureOkResponse(
  res: Response,
  fallbackErrorMessage?: string,
): Promise<Response> {
  if (res.ok) return res;

  const message = await parseApiErrorMessage(
    res,
    fallbackErrorMessage ?? 'Request failed',
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

export async function requestVoid(
  path: string,
  options: RequestOptions = {},
): Promise<void> {
  const res = await executeRequest(path, options);
  await ensureOkResponse(res, options.fallbackErrorMessage);
}
