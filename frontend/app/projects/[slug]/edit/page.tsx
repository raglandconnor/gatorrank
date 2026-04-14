'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Spinner,
  Input,
} from '@chakra-ui/react';
import { LuSave, LuX } from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import {
  ProjectForm,
  ProjectFormValues,
  ProjectPayload,
} from '@/components/projects/ProjectForm';
import {
  addProjectMember,
  deleteProject,
  getProject,
  getProjectBySlug,
  publishProject,
  removeProjectMember,
  unpublishProject,
  updateProject,
} from '@/lib/api/projects';
import type { ProjectDetail, ProjectMemberInfo } from '@/lib/api/types/project';
import { isUuid } from '@/lib/profileSlug';
import { projectEditPath, projectPath } from '@/lib/routes';
import { toast } from '@/lib/ui/toast';

type LoadState =
  | { status: 'loading' }
  | { status: 'notfound' }
  | { status: 'forbidden' }
  | { status: 'error'; message: string }
  | { status: 'ready'; project: ProjectDetail };

function toFormValues(project: ProjectDetail): ProjectFormValues {
  return {
    title: project.title,
    shortDescription: project.short_description,
    fullDescription: project.long_description ?? '',
    imageUrl: null,
    tags: project.tags.map((tag) => tag.name),
    websiteUrl: project.demo_url ?? '',
    githubUrl: project.github_url ?? '',
    demoVideoUrl: project.video_url ?? '',
  };
}

export default function EditProjectPage() {
  const router = useRouter();
  const { slug } = useParams<{ slug: string }>();
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [isSubmitDisabled, setIsSubmitDisabled] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteTitleInput, setDeleteTitleInput] = useState('');
  const [members, setMembers] = useState<ProjectMemberInfo[]>([]);
  const [shouldPublish, setShouldPublish] = useState(true);

  useEffect(() => {
    async function loadProject() {
      try {
        const project = isUuid(slug)
          ? await getProject(slug)
          : await getProjectBySlug(slug);
        setMembers(project.members);
        setShouldPublish(project.is_published);
        setState({ status: 'ready', project });
        if (project.slug !== slug) {
          router.replace(projectEditPath(project.slug));
        }
      } catch (error) {
        const status =
          error instanceof Error && 'status' in error
            ? Number((error as Error & { status?: number }).status)
            : null;

        if (status === 404) {
          setState({ status: 'notfound' });
          return;
        }
        if (status === 403) {
          setState({ status: 'forbidden' });
          return;
        }

        setState({
          status: 'error',
          message:
            error instanceof Error ? error.message : 'Could not load project.',
        });
      }
    }

    void loadProject();
  }, [router, slug]);

  const initialValues = useMemo<ProjectFormValues>(() => {
    if (state.status !== 'ready') {
      return {
        title: '',
        shortDescription: '',
        fullDescription: '',
        imageUrl: null,
        tags: [],
        websiteUrl: '',
        githubUrl: '',
        demoVideoUrl: '',
      };
    }
    return toFormValues(state.project);
  }, [state]);

  const handleSubmit = async (payload: ProjectPayload) => {
    if (state.status !== 'ready') return;

    setIsSubmitting(true);
    try {
      let project = await updateProject(state.project.id, payload);
      if (shouldPublish && !project.is_published) {
        project = await publishProject(project.id);
      } else if (!shouldPublish && project.is_published) {
        project = await unpublishProject(project.id);
      }

      setMembers(project.members);
      setShouldPublish(project.is_published);
      setState({ status: 'ready', project });
      toast.success({
        title: 'Project updated',
        description: `"${project.title}" has been successfully updated.`,
      });
      router.push(projectPath(project.slug));
    } catch (error) {
      toast.error({
        title: 'Could not update project',
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (state.status === 'ready') {
      router.push(projectPath(state.project.slug));
    }
  };

  const expectedDeleteTitle =
    state.status === 'ready' ? state.project.title.trim() : '';
  const isDeleteTitleMatch =
    deleteTitleInput.trim().toLowerCase() ===
      expectedDeleteTitle.toLowerCase() && expectedDeleteTitle.length > 0;

  const openDeleteModal = () => {
    if (isSubmitting || isDeleting) return;
    setDeleteTitleInput('');
    setIsDeleteModalOpen(true);
  };

  const closeDeleteModal = () => {
    if (isDeleting) return;
    setDeleteTitleInput('');
    setIsDeleteModalOpen(false);
  };

  const handleDeleteProject = async () => {
    if (state.status !== 'ready') return;
    if (isSubmitting || isDeleting || !isDeleteTitleMatch) return;

    setIsDeleting(true);
    try {
      await deleteProject(state.project.id);
      toast.success({
        title: 'Project deleted',
        description: 'Your project has been deleted.',
      });
      setIsDeleteModalOpen(false);
      router.push('/profile');
    } catch (error) {
      toast.error({
        title: 'Could not delete project',
        description:
          error instanceof Error ? error.message : 'Please try again.',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  if (state.status === 'loading') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="lg" color="orange.400" />
        </Flex>
      </Box>
    );
  }

  if (state.status === 'notfound' || state.status === 'forbidden') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex
          justify="center"
          align="center"
          minH="60vh"
          direction="column"
          gap="12px"
        >
          <Text color="gray.600">
            {state.status === 'notfound'
              ? 'This project does not exist.'
              : 'You do not have permission to edit this project.'}
          </Text>
          <Button
            bg="orange.400"
            color="white"
            _hover={{ bg: 'orange.500' }}
            onClick={() => router.push('/')}
          >
            Go home
          </Button>
        </Flex>
      </Box>
    );
  }

  if (state.status === 'error') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex
          justify="center"
          align="center"
          minH="60vh"
          direction="column"
          gap="12px"
        >
          <Text color="gray.600">{state.message}</Text>
          <Button
            bg="orange.400"
            color="white"
            _hover={{ bg: 'orange.500' }}
            onClick={() => router.refresh()}
          >
            Try again
          </Button>
        </Flex>
      </Box>
    );
  }

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
                <LuSave size={16} />
                <Text>{isSubmitting ? 'Saving...' : 'Save Changes'}</Text>
              </HStack>
            </Button>
          </HStack>
        </Flex>

        <ProjectForm
          key={`${state.project.id}:${state.project.updated_at}`}
          mode="edit"
          initialValues={initialValues}
          onSubmit={handleSubmit}
          onValidityChange={setIsSubmitDisabled}
          publishChecked={shouldPublish}
          onPublishCheckedChange={setShouldPublish}
          members={members}
          pendingMemberEmails={[]}
          isBusy={isSubmitting}
          onAddMember={async (email) => {
            try {
              const member = await addProjectMember(state.project.id, {
                email,
              });
              setMembers((prev) => [...prev, member]);
              return { ok: true as const };
            } catch (error) {
              return {
                ok: false as const,
                message:
                  error instanceof Error
                    ? error.message
                    : 'Could not add project member.',
              };
            }
          }}
          onRemoveMember={async (userId) => {
            try {
              await removeProjectMember(state.project.id, userId);
              setMembers((prev) =>
                prev.filter((member) => member.user_id !== userId),
              );
              return { ok: true as const };
            } catch (error) {
              return {
                ok: false as const,
                message:
                  error instanceof Error
                    ? error.message
                    : 'Could not remove project member.',
              };
            }
          }}
        />

        <Box
          mt="36px"
          p="20px"
          borderRadius="14px"
          border="1px solid"
          borderColor="red.200"
          bg="red.50"
        >
          <VStack align="start" gap="10px">
            <Text fontSize="md" fontWeight="bold" color="red.700">
              Delete project
            </Text>
            <Text fontSize="sm" color="red.700">
              This action cannot be undone.
            </Text>
            <Button
              type="button"
              bg="red.600"
              color="white"
              _hover={{ bg: 'red.700' }}
              disabled={isSubmitting || isDeleting}
              onClick={openDeleteModal}
            >
              Delete Project
            </Button>
          </VStack>
        </Box>

        {isDeleteModalOpen && (
          <Box
            position="fixed"
            inset={0}
            bg="blackAlpha.600"
            zIndex={1500}
            display="flex"
            alignItems="center"
            justifyContent="center"
            px="16px"
          >
            <Box
              role="dialog"
              aria-modal="true"
              bg="white"
              borderRadius="16px"
              border="1px solid"
              borderColor="gray.200"
              p="20px"
              w="100%"
              maxW="520px"
            >
              <VStack align="start" gap="12px">
                <Text fontSize="lg" fontWeight="bold" color="gray.900">
                  Delete project
                </Text>
                <Text fontSize="sm" color="gray.700">
                  Type{' '}
                  <Text as="span" fontWeight="bold">
                    {state.project.title}
                  </Text>{' '}
                  to confirm. This action cannot be undone.
                </Text>
                <Input
                  value={deleteTitleInput}
                  onChange={(event) => setDeleteTitleInput(event.target.value)}
                  placeholder={state.project.title}
                  aria-label="Type project title to confirm deletion"
                  disabled={isDeleting}
                />
                <HStack justify="flex-end" w="100%" gap="10px">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={closeDeleteModal}
                    disabled={isDeleting}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    bg="red.600"
                    color="white"
                    _hover={{ bg: 'red.700' }}
                    disabled={!isDeleteTitleMatch || isDeleting}
                    onClick={() => void handleDeleteProject()}
                  >
                    {isDeleting ? 'Deleting...' : 'Delete Project'}
                  </Button>
                </HStack>
              </VStack>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
