'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { GatorRankLogo } from '@/components/layout/GatorRankLogo';
import { toast } from '@/lib/ui/toast';
import { Flex, Heading, Stack, Text } from '@chakra-ui/react';
import { LoginFormPanel } from '@/components/auth/LoginFormPanel';

type LoginPageClientProps = {
  signedOut: boolean;
  returnTo: string | null;
};

export function LoginPageClient({ signedOut, returnTo }: LoginPageClientProps) {
  const router = useRouter();

  useEffect(() => {
    if (!signedOut) return;
    toast.success({
      title: 'Signed out',
      description: 'You have been successfully signed out.',
    });
    router.replace('/login');
  }, [signedOut, router]);

  return (
    <Flex
      minH="100vh"
      bg="transparent"
      direction="column"
      align="center"
      justify="flex-start"
      py={{ base: 4, sm: 6 }}
      px={{ base: 4, sm: 6 }}
    >
      <Stack
        gap={{ base: 6, sm: 8 }}
        width="100%"
        maxW="400px"
        align="center"
        textAlign="center"
      >
        <Stack gap={0} align="center">
          <GatorRankLogo />
          <Stack gap={1}>
            <Heading
              size={{ base: 'xl', sm: '2xl' }}
              fontWeight="700"
              color="gray.800"
            >
              Welcome Back
            </Heading>
            <Text fontSize={{ base: 'sm', sm: 'md' }} color="gray.600">
              Sign in to access your projects
            </Text>
          </Stack>
        </Stack>

        <LoginFormPanel returnTo={returnTo} />
      </Stack>
    </Flex>
  );
}
