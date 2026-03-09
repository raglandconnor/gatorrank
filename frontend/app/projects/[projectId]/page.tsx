'use client';

import { useParams, useRouter } from 'next/navigation';
import { Box, VStack, Text, Button, HStack } from '@chakra-ui/react';
import { Navbar } from '@/components/Navbar';

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  return (
    <Box minH="100vh" bg="white">
      <Navbar />
      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        <VStack align="start" gap="24px">
          <Text fontSize="2xl" fontWeight="bold" color="gray.900">
            Project
          </Text>
          <Text fontSize="md" color="gray.600">
            Project ID: {projectId}
          </Text>
          <HStack gap="12px">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/profile')}
            >
              Back to Profile
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/projects/edit')}
            >
              Edit Project
            </Button>
          </HStack>
        </VStack>
      </Box>
    </Box>
  );
}
