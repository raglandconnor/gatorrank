export interface HttpError extends Error {
  status: number;
}

export async function parseApiErrorMessage(
  res: Response,
  fallback: string,
): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: unknown };
    const detail = data.detail;

    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            item &&
            typeof item === 'object' &&
            'msg' in item &&
            typeof item.msg === 'string'
          ) {
            return item.msg;
          }
          return null;
        })
        .filter((message): message is string => Boolean(message));

      if (messages.length > 0) {
        return messages.join('; ');
      }
    }
  } catch {
    // Ignore parse failures and fall back to generic text.
  }

  return res.statusText || fallback;
}

export function buildHttpError(message: string, status: number): HttpError {
  const error = new Error(message) as HttpError;
  error.status = status;
  return error;
}

export function buildQueryString(
  query: Record<string, string | number | boolean | undefined>,
): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === '') continue;
    params.set(key, String(value));
  }

  const qs = params.toString();
  return qs ? `?${qs}` : '';
}
