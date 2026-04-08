'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Flex, Spinner } from '@chakra-ui/react';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/components/domain/AuthProvider';

/** Redirects `/profile/edit` to the canonical `/profile/{userId}/edit`. */
export default function ProfileEditIndexPage() {
  const router = useRouter();
  const { user, isReady } = useAuth();

  useEffect(() => {
    if (!isReady) return;
    if (!user) {
      router.replace('/login');
      return;
    }
    router.replace(`/profile/${user.id}/edit`);
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
