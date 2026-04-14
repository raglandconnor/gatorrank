import { describe, expect, test } from 'vitest';

import { getSafePostAuthRedirectPath } from '@/lib/supabase/redirect';

describe('getSafePostAuthRedirectPath', () => {
  test('allows same-origin relative paths', () => {
    expect(getSafePostAuthRedirectPath('/')).toBe('/');
    expect(getSafePostAuthRedirectPath('/profile')).toBe('/profile');
    expect(getSafePostAuthRedirectPath('/projects?sort=top')).toBe(
      '/projects?sort=top',
    );
  });

  test('falls back for missing/invalid next values', () => {
    expect(getSafePostAuthRedirectPath(null)).toBe('/login');
    expect(getSafePostAuthRedirectPath('')).toBe('/login');
    expect(getSafePostAuthRedirectPath('profile')).toBe('/login');
    expect(getSafePostAuthRedirectPath('https://attacker.example')).toBe(
      '/login',
    );
    expect(getSafePostAuthRedirectPath('//attacker.example')).toBe('/login');
  });
});
