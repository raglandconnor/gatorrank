import { describe, expect, test } from 'vitest';
import LoginPage from '@/app/login/page';

describe('LoginPage server param parsing', () => {
  test('maps signedOut and returnTo string values into client props', async () => {
    const element = await LoginPage({
      searchParams: Promise.resolve({
        signedOut: '1',
        returnTo: '/projects/search?q=ai&sort=top',
      }),
    });

    expect(element.props.signedOut).toBe(true);
    expect(element.props.returnTo).toBe('/projects/search?q=ai&sort=top');
  });

  test('ignores non-string returnTo and non-1 signedOut values', async () => {
    const element = await LoginPage({
      searchParams: Promise.resolve({
        signedOut: '0',
        returnTo: ['/projects/search'],
      }),
    });

    expect(element.props.signedOut).toBe(false);
    expect(element.props.returnTo).toBeNull();
  });

  test('defaults to signedOut=false and returnTo=null when params missing', async () => {
    const element = await LoginPage({
      searchParams: Promise.resolve({}),
    });

    expect(element.props.signedOut).toBe(false);
    expect(element.props.returnTo).toBeNull();
  });
});
