'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Flex, HStack, VStack, Text, Button } from '@chakra-ui/react';
import { LuX, LuSave } from 'react-icons/lu';
import { Navbar } from '@/components/Navbar';
import {
  ProjectForm,
  ProjectFormValues,
  ProjectPayload,
} from '@/components/projects/ProjectForm';
import { toaster } from '@/components/ui/toaster';
import { mockProject } from '@/data/mock-project';

export default function EditProjectPage() {
  const router = useRouter();
  const [isSubmitDisabled, setIsSubmitDisabled] = useState(false);

  const initialValues: ProjectFormValues = {
    name: mockProject.name,
    shortDescription: mockProject.shortDescription,
    fullDescription: mockProject.fullDescription,
    imageUrl: mockProject.imageUrl ?? null,
    tags: mockProject.tags,
    teamMembers: mockProject.teamMembers,
    websiteUrl: mockProject.websiteUrl,
    githubUrl: mockProject.githubUrl,
    demoVideoUrl: mockProject.demoVideoUrl,
  };

  const handleSubmit = (payload: ProjectPayload) => {
    toaster.success({
      title: 'Project updated',
      description: `"${payload.name}" has been successfully updated.`,
    });

    router.push(`/projects/${mockProject.id}`);
  };

  const handleCancel = () => {
    router.push(`/projects/${mockProject.id}`);
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
              Edit Project
            </Text>
            <Text fontSize="sm" color="gray.600" lineHeight="24px" maxW="520px">
              Update your project details for the GatorRank community.
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
              onClick={handleCancel}
            >
              <HStack gap="6px">
                <LuX size={16} />
                <Text>Cancel</Text>
              </HStack>
            </Button>
            <Button
              type="submit"
              form="project-form"
              bg={isSubmitDisabled ? 'gray.300' : 'orange.400'}
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              fontWeight="normal"
              _hover={{ bg: isSubmitDisabled ? 'gray.300' : 'orange.500' }}
              transition="background 0.15s"
              disabled={isSubmitDisabled}
              cursor={isSubmitDisabled ? 'not-allowed' : 'pointer'}
            >
              <HStack gap="6px">
                <LuSave size={16} />
                <Text>Save Changes</Text>
              </HStack>
            </Button>
          </HStack>
        </Flex>

        {/* Form */}
        <ProjectForm
          mode="edit"
          initialValues={initialValues}
          onSubmit={handleSubmit}
          onValidityChange={setIsSubmitDisabled}
        />
      </Box>
    </Box>
  );
}
