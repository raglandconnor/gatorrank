/**
 * Maps raw API error messages for auth flows to user-facing toast copy.
 * Titles are calm and human. Descriptions give a concrete next step while
 * preserving useful server detail when it's truly informative.
 */

interface AuthToastContent {
  title: string;
  description: string;
}

/** Normalised phrases and the description we show for each. */
const LOGIN_PATTERNS: Array<[RegExp, string]> = [
  [
    /incorrect|invalid|unauthorized|wrong|bad credential|not found/i,
    'Double-check your email and password and try again.',
  ],
  [
    /locked|too many|rate.?limit/i,
    'Too many failed attempts. Please wait a few minutes before trying again.',
  ],
  [
    /network|fetch|connect|unreachable/i,
    'Could not reach the server. Check your connection and try again.',
  ],
];

const SIGNUP_PATTERNS: Array<[RegExp, string]> = [
  [
    /already.?(exists|registered)|duplicate|conflict/i,
    'An account with this email already exists. Try signing in instead.',
  ],
  [
    /password.*too short|at least.*character/i,
    'Your password needs to be at least 12 characters long.',
  ],
  [/email.*invalid|not.*edu/i, 'Please use a valid email address to register.'],
  [
    /network|fetch|connect|unreachable/i,
    'Could not reach the server. Check your connection and try again.',
  ],
];

function matchDescription(
  rawMessage: string,
  patterns: Array<[RegExp, string]>,
  fallback: string,
): string {
  for (const [re, copy] of patterns) {
    if (re.test(rawMessage)) return copy;
  }
  return fallback;
}

export function loginErrorToast(err: unknown): AuthToastContent {
  const raw = err instanceof Error ? err.message : String(err);
  return {
    title: "We couldn't sign you in",
    description: matchDescription(
      raw,
      LOGIN_PATTERNS,
      'Check your email and password, then try again.',
    ),
  };
}

export function signupErrorToast(err: unknown): AuthToastContent {
  const raw = err instanceof Error ? err.message : String(err);
  return {
    title: "We couldn't create your account",
    description: matchDescription(
      raw,
      SIGNUP_PATTERNS,
      'Something went wrong. Please check your details and try again.',
    ),
  };
}
