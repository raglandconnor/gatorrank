import { NextResponse } from 'next/server';

import { getSafePostAuthRedirectPath } from '@/lib/supabase/redirect';
import { createSupabaseServerClient } from '@/lib/supabase/server';

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const returnTo = getSafePostAuthRedirectPath(
    requestUrl.searchParams.get('next'),
  );

  if (code) {
    const supabase = await createSupabaseServerClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  return NextResponse.redirect(new URL(returnTo, requestUrl.origin));
}
