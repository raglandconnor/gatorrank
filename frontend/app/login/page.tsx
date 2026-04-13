import { LoginPageClient } from '@/components/auth/LoginPageClient';

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = (await searchParams) ?? {};
  const signedOut = params.signedOut === '1';
  const returnTo = typeof params.returnTo === 'string' ? params.returnTo : null;

  return <LoginPageClient signedOut={signedOut} returnTo={returnTo} />;
}
