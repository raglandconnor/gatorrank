'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Flex, HStack, VStack, Text, Button } from '@chakra-ui/react';
import { LuImage, LuX } from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import {
  ProjectForm,
  ProjectFormValues,
  ProjectPayload,
} from '@/components/projects/ProjectForm';
import {
  addProjectMember,
  createProject,
  publishProject,
} from '@/lib/api/projects';
import { projectPath } from '@/lib/routes';
import { toast } from '@/lib/ui/toast';

export default function CreateProjectPage() {
  const router = useRouter();
  const [isSubmitDisabled, setIsSubmitDisabled] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingMemberEmails, setPendingMemberEmails] = useState<string[]>([]);
  const [shouldPublish, setShouldPublish] = useState(true);

  const initialValues = useMemo<ProjectFormValues>(
    () => ({
      title: '',
      shortDescription: '',
      fullDescription: '',
      imageUrl: null,
      tags: [],
      websiteUrl: '',
      githubUrl: '',
      demoVideoUrl: '',
    }),
    [],
  );

  const handleSubmit = async (payload: ProjectPayload) => {
    setIsSubmitting(true);

    try {
      let project = await createProject(payload);

      if (shouldPublish) {
        project = await publishProject(project.id);
      }

      const memberResults = await Promise.all(
        pendingMemberEmails.map(async (email) => {
          try {
            await addProjectMember(project.id, { email });
            return { email, ok: true as const };
          } catch (error) {
            return {
              email,
              ok: false as const,
              message:
                error instanceof Error
                  ? error.message
                  : 'Could not add project member.',
            };
          }
        }),
      );

      const failedAdds = memberResults.filter((result) => !result.ok);

      if (failedAdds.length > 0) {
        const descriptions = failedAdds
          .map((result) => `${result.email}: ${result.message}`)
          .join('\n');

        toast.warning({
          title: 'Project created with some member errors',
          description: descriptions,
          duration: 9000,
        });
      } else if (project.is_published) {
        toast.success({
          title: 'Project created',
          description: `"${project.title}" has been created and published.`,
        });
      } else {
        toast.success({
          title: 'Project saved as draft',
          description: `"${project.title}" has been created as a draft.`,
        });
      }

      router.push(projectPath(project.slug));
    } catch (error) {
      toast.error({
        title: 'Could not create project',
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
      setIsSubmitting(false);
    }
  };

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />
      <Box
        px={{ base: '16px', md: '24px', lg: '36px' }}
        pt="32px"
        pb="64px"
        maxW="1280px"
        mx="auto"
      >
        <Flex
          align="flex-start"
          justify="space-between"
          mb="32px"
          gap="16px"
          flexWrap="wrap"
        >
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
              disabled={isSubmitting}
            >
              <HStack gap="6px">
                <LuX size={16} />
                <Text>Cancel</Text>
              </HStack>
            </Button>
            <Button
              type="submit"
              form="project-form"
              bg={isSubmitDisabled || isSubmitting ? 'gray.300' : 'orange.400'}
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              fontWeight="normal"
              _hover={{
                bg:
                  isSubmitDisabled || isSubmitting ? 'gray.300' : 'orange.500',
              }}
              transition="background 0.15s"
              disabled={isSubmitDisabled || isSubmitting}
              cursor={
                isSubmitDisabled || isSubmitting ? 'not-allowed' : 'pointer'
              }
            >
              <HStack gap="6px">
                <LuImage size={16} />
                <Text>{isSubmitting ? 'Creating...' : 'Submit Project'}</Text>
              </HStack>
            </Button>
          </HStack>
        </Flex>

        <ProjectForm
          mode="create"
          initialValues={initialValues}
          onSubmit={handleSubmit}
          onValidityChange={setIsSubmitDisabled}
          publishChecked={shouldPublish}
          onPublishCheckedChange={setShouldPublish}
          members={[]}
          pendingMemberEmails={pendingMemberEmails}
          isBusy={isSubmitting}
          onAddMember={async (email) => {
            if (pendingMemberEmails.includes(email)) {
              return { ok: false as const, message: 'Member already added.' };
            }
            setPendingMemberEmails((prev) => [...prev, email]);
            return { ok: true as const };
          }}
          onRemoveMember={async (email) => {
            setPendingMemberEmails((prev) =>
              prev.filter((memberEmail) => memberEmail !== email),
            );
            return { ok: true as const };
          }}
        />
      </Box>
    </Box>
  );
}
