import { describe, expect, test } from 'vitest';
import {
  buildReturnToFromWindow,
  resolveSafeReturnTo,
} from '@/lib/auth/returnTo';

describe('returnTo helpers', () => {
  test('buildReturnToFromWindow includes path and query', () => {
    window.history.replaceState({}, '', '/projects/search?q=ai&sort=top');

    expect(buildReturnToFromWindow()).toBe('/projects/search?q=ai&sort=top');
  });

  test('resolveSafeReturnTo accepts in-app paths only', () => {
    expect(resolveSafeReturnTo('/projects/p1')).toBe('/projects/p1');
    expect(resolveSafeReturnTo('https://evil.example')).toBe('/profile');
    expect(resolveSafeReturnTo('//evil.example')).toBe('/profile');
    expect(resolveSafeReturnTo(undefined, '/')).toBe('/');
  });
});
