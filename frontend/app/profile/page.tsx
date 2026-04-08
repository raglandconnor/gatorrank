'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Flex, Spinner } from '@chakra-ui/react';
import { Navbar } from '@/components/Navbar';
import { useAuth } from '@/components/auth/AuthProvider';
import { profilePath } from '@/lib/routes';

/** Redirects `/profile` to the canonical `/profile/{username}`. */
export default function ProfileIndexPage() {
  const router = useRouter();
  const { user, isReady } = useAuth();

  useEffect(() => {
    if (!isReady) return;
    if (!user) {
      router.replace('/login');
      return;
    }
    router.replace(profilePath(user.username));
  }, [isReady, user, router]);

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />
      <Flex justify="center" align="center" minH="60vh">
        <Spinner size="lg" color="orange.400" />
      </Flex>
    </Box>
  );
}
