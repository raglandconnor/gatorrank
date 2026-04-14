const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/i;
const NAME_REGEX = /^[a-zA-Z\s\-'']+$/;

export function isValidEmail(email: string): boolean {
  if (!email.trim()) return false;
  return EMAIL_REGEX.test(email.trim());
}

export function isValidName(name: string): boolean {
  if (!name.trim()) return false;
  return NAME_REGEX.test(name.trim());
}

/**
 * Matches backend `AuthService.validate_password_policy`
 * (`backend/app/services/auth.py`, also enforced via `backend/app/schemas/auth.py`).
 */
export function isValidPassword(password: string): boolean {
  if (password.trim() === '') return false;
  if (password.length < 12) return false;
  if (password.length > 128) return false;
  return true;
}
