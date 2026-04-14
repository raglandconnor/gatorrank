import { describe, expect, test } from 'vitest';
import { isValidEmail, isValidName, isValidPassword } from '@/lib/validation';

describe('validation utilities', () => {
  test('validates email addresses', () => {
    expect(isValidEmail('student@ufl.edu')).toBe(true);
    expect(isValidEmail('student@gmail.com')).toBe(true);
    expect(isValidEmail(' student@gmail.com ')).toBe(true);
    expect(isValidEmail('not-an-email')).toBe(false);
    expect(isValidEmail('')).toBe(false);
  });

  test('validates user names', () => {
    expect(isValidName("O'Neil-Smith")).toBe(true);
    expect(isValidName('Jane Doe')).toBe(true);
    expect(isValidName('Jane123')).toBe(false);
    expect(isValidName('')).toBe(false);
  });

  test('enforces password length policy', () => {
    expect(isValidPassword('123456789012')).toBe(true);
    expect(isValidPassword(' '.repeat(12))).toBe(false);
    expect(isValidPassword('short')).toBe(false);
    expect(isValidPassword('a'.repeat(129))).toBe(false);
  });
});
