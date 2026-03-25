const EDU_EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.edu$/i;
const NAME_REGEX = /^[a-zA-Z\s\-'']+$/;

export function isValidEduEmail(email: string): boolean {
  if (!email.trim()) return false;
  return EDU_EMAIL_REGEX.test(email.trim());
}

export function isValidName(name: string): boolean {
  if (!name.trim()) return false;
  return NAME_REGEX.test(name.trim());
}

/** Matches backend password policy: 12–128 chars, not whitespace-only. */
export function isValidPassword(password: string): boolean {
  const t = password.trim();
  if (t.length === 0) return false;
  if (t.length < 12) return false;
  if (t.length > 128) return false;
  return true;
}
