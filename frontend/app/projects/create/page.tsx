'use client';

import { useRouter } from 'next/navigation';
import { Box, Flex, HStack, VStack, Text, Button } from '@chakra-ui/react';
import { LuX, LuImage } from 'react-icons/lu';
import { Navbar } from '@/components/Navbar';
import {
  ProjectForm,
  ProjectFormValues,
  ProjectPayload,
} from '@/components/projects/ProjectForm';
import { toaster } from '@/components/ui/toaster';

export default function CreateProjectPage() {
  const router = useRouter();

  const initialValues: ProjectFormValues = {
    name: '',
    shortDescription: '',
    fullDescription: '',
    imageUrl: null,
    tags: [],
    teamMembers: [],
    websiteUrl: '',
    githubUrl: '',
    demoVideoUrl: '',
  };

  const handleSubmit = (payload: ProjectPayload) => {
    // For now, just log payload for future backend integration.
    // eslint-disable-next-line no-console
    console.log('Create project payload:', payload);

    toaster.success({
      title: 'Project created',
      description: `"${payload.name}" has been successfully created.`,
    });

    router.push('/profile');
  };

  return (
    <Box minH="100vh" bg="white">
      <Navbar />
      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        {/* Header */}
        <Flex align="flex-start" justify="space-between" mb="32px" gap="16px">
          <VStack align="start" gap="6px">
            <Text
              fontSize="xl"
              fontWeight="bold"
              color="gray.900"
              lineHeight="32px"
            >
              Create Project
            </Text>
            <Text fontSize="sm" color="gray.600" lineHeight="24px" maxW="520px">
              Share your work with the GatorRank community.
            </Text>
          </VStack>

          <HStack gap="12px" flexShrink={0}>
            <Button
              type="button"
              variant="outline"
              border="1px solid"
              borderColor="orange.400"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              color="gray.900"
              bg="white"
              _hover={{ bg: 'orange.50' }}
              transition="background 0.15s"
              onClick={() => router.push('/profile')}
            >
              <HStack gap="6px">
                <LuX size={16} />
                <Text>Cancel</Text>
              </HStack>
            </Button>
            <Button
              type="submit"
              form="project-form"
              bg="orange.400"
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              fontWeight="normal"
              _hover={{ bg: 'orange.500' }}
              transition="background 0.15s"
            >
              <HStack gap="6px">
                <LuImage size={16} />
                <Text>Submit Project</Text>
              </HStack>
            </Button>
          </HStack>
        </Flex>

        {/* Form */}
        <ProjectForm
          mode="create"
          initialValues={initialValues}
          submitLabel="Submit Project"
          onSubmit={handleSubmit}
        />
      </Box>
    </Box>
  );
}
