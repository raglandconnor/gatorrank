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

export function isValidPassword(password: string): boolean {
  if (password.length < 10) return false;
  if (!/[A-Z]/.test(password)) return false;
  if (!/[a-z]/.test(password)) return false;
  if (!/[0-9]/.test(password)) return false;
  if (!/[^A-Za-z0-9]/.test(password)) return false;
  return true;
}
