import { describe, expect, test } from 'vitest';
import {
  isValidEduEmail,
  isValidName,
  isValidPassword,
} from '@/lib/validation';

describe('validation utilities', () => {
  test('validates .edu emails', () => {
    expect(isValidEduEmail('student@ufl.edu')).toBe(true);
    expect(isValidEduEmail(' student@ufl.edu ')).toBe(true);
    expect(isValidEduEmail('student@gmail.com')).toBe(false);
    expect(isValidEduEmail('')).toBe(false);
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
