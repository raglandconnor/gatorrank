'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Badge,
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  Link as ChakraLink,
} from '@chakra-ui/react';
import {
  LuGithub,
  LuVideo,
  LuPlay,
  LuExternalLink,
  LuPencil,
  LuFileText,
  LuSkipBack,
  LuSkipForward,
  LuVolume2,
  LuSettings2,
  LuExpand,
} from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import { useAuth } from '@/components/domain/AuthProvider';
import { UpvoteBox } from '@/components/projects/UpvoteBox';
import {
  getProjectByIdForViewer,
  getProjectBySlugForViewer,
} from '@/lib/api/projects';
import type { ProjectDetail } from '@/lib/api/types/project';
import { isUuid } from '@/lib/profileSlug';
import { profilePath, projectEditPath, projectPath } from '@/lib/routes';
import { ProjectLogoPlaceholder } from '@/components/projects/ProjectLogoPlaceholder';
import { FeatureLoadingState } from '@/components/ui/FeatureLoadingState';
import { UserAvatar } from '@/components/ui/UserAvatar';

function getYouTubeEmbedUrl(url: string): string | null {
  const trimmed = url.trim();
  if (!trimmed) return null;

  try {
    const parsed = new URL(trimmed);
    const host = parsed.hostname.replace(/^www\./, '').toLowerCase();
    let videoId = '';

    if (host === 'youtu.be') {
      videoId = parsed.pathname.split('/').filter(Boolean)[0] ?? '';
    } else if (host === 'youtube.com' || host === 'm.youtube.com') {
      if (parsed.pathname === '/watch') {
        videoId = parsed.searchParams.get('v') ?? '';
      } else if (parsed.pathname.startsWith('/shorts/')) {
        videoId = parsed.pathname.split('/')[2] ?? '';
      } else if (parsed.pathname.startsWith('/embed/')) {
        videoId = parsed.pathname.split('/')[2] ?? '';
      }
    }

    const videoIdRegex = /^[a-zA-Z0-9_-]{11}$/;
    if (!videoId) return null;
    const normalizedVideoId = videoId.trim();
    if (!videoIdRegex.test(normalizedVideoId)) return null;

    return `https://www.youtube.com/embed/${encodeURIComponent(normalizedVideoId)}`;
  } catch {
    return null;
  }
}

function MemberMetaBlock({
  username,
  fullName,
  profilePictureUrl,
  description,
  onClick,
}: {
  username: string;
  fullName: string | null;
  profilePictureUrl: string | null;
  description: string;
  onClick: () => void;
}) {
  return (
    <HStack
      gap="12px"
      cursor="pointer"
      transition="background 0.15s, border-color 0.15s, box-shadow 0.15s, transform 0.15s"
      _hover={{
        bg: 'white',
        borderColor: 'orange.200',
        boxShadow: '0 10px 24px rgba(251,146,60,0.12)',
        transform: 'translateY(-1px)',
      }}
      _focusWithin={{
        bg: 'white',
        borderColor: 'orange.200',
        boxShadow: '0 0 0 3px rgba(251,146,60,0.16)',
      }}
      onClick={onClick}
      minW="fit-content"
      border="1px solid"
      borderColor="transparent"
      borderRadius="14px"
      px="10px"
      py="8px"
      bg="transparent"
    >
      <UserAvatar
        name={fullName ?? username}
        imageUrl={profilePictureUrl}
        size="52px"
        fontSize="md"
      />
      <VStack align="start" gap="2px" minW={0}>
        <Text
          fontSize="md"
          fontWeight="bold"
          color="gray.900"
          lineHeight="22px"
          lineClamp={1}
        >
          {fullName ?? username}
        </Text>
        <Text fontSize="sm" color="gray.600" lineHeight="18px" lineClamp={1}>
          {description}
        </Text>
      </VStack>
    </HStack>
  );
}

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const { accessToken, isReady, user } = useAuth();
  const slug = params.slug;
  const [projectDetail, setProjectDetail] = useState<ProjectDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const requestIdRef = useRef(0);

  const loadProject = useCallback(async () => {
    if (!isReady) return;
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError(null);
    setNotFound(false);
    setForbidden(false);

    try {
      const detail = isUuid(slug)
        ? await getProjectByIdForViewer(slug, accessToken)
        : await getProjectBySlugForViewer(slug, accessToken);
      if (requestId !== requestIdRef.current) return;
      setProjectDetail(detail);
      if (detail.slug !== slug) {
        router.replace(projectPath(detail.slug));
      }
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      const status =
        typeof err === 'object' &&
        err !== null &&
        'status' in err &&
        typeof (err as { status?: unknown }).status === 'number'
          ? (err as { status: number }).status
          : null;

      if (status === 404) {
        setNotFound(true);
        setProjectDetail(null);
        return;
      }

      if (status === 403) {
        setForbidden(true);
        setProjectDetail(null);
        return;
      }

      setError(
        err instanceof Error ? err.message : 'Failed to load project detail.',
      );
      setProjectDetail(null);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [accessToken, isReady, router, slug]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const project = projectDetail;
  const isOwner = user?.id === project?.created_by_id;
  const projectMembers = useMemo(() => {
    if (!projectDetail?.members.length) return [];
    return [...projectDetail.members].sort((left, right) => {
      if (left.role === 'owner' && right.role !== 'owner') return -1;
      if (left.role !== 'owner' && right.role === 'owner') return 1;
      return (left.full_name ?? left.username).localeCompare(
        right.full_name ?? right.username,
      );
    });
  }, [projectDetail]);
  const projectCreator = projectMembers[0] ?? null;
  const nonOwnerMembers = projectMembers.slice(1);
  const isProjectMember = useMemo(() => {
    if (!user?.id || !projectDetail?.members.length) return false;
    return projectDetail.members.some((member) => member.user_id === user.id);
  }, [projectDetail, user?.id]);
  const canSeePublishStateBadge = Boolean(user?.id) && (isOwner || isProjectMember);

  if (!isReady || loading) {
    return (
      <Box minH="100vh" bg="gray.50">
        <Navbar />
        <Box
          px={{ base: '20px', md: '32px' }}
          pt="32px"
          pb="64px"
          maxW="1200px"
          mx="auto"
        >
          <FeatureLoadingState
            title="Loading project"
            description="Pulling in the latest project details, links, and tags."
            icon={<LuVideo size={24} />}
          />
        </Box>
      </Box>
    );
  }

  if (notFound || forbidden) {
    return (
      <Box minH="100vh" bg="gray.50">
        <Navbar />
        <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
          <Flex
            minH="50vh"
            align="center"
            justify="center"
            direction="column"
            gap="24px"
          >
            <Text fontSize="lg" color="gray.600">
              {notFound
                ? 'Project not found'
                : 'You do not have access to this project.'}
            </Text>
            <Button
              bg="orange.400"
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              _hover={{ bg: 'orange.500' }}
              onClick={() => router.push('/profile')}
            >
              Back to profile
            </Button>
          </Flex>
        </Box>
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Box minH="100vh" bg="gray.50">
        <Navbar />
        <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
          <Flex
            minH="50vh"
            align="center"
            justify="center"
            direction="column"
            gap="18px"
          >
            <Text fontSize="lg" color="red.500">
              {error ?? 'Failed to load project detail.'}
            </Text>
            <Button
              type="button"
              onClick={() => void loadProject()}
              bg="gray.900"
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              _hover={{ bg: 'gray.700' }}
            >
              Retry
            </Button>
          </Flex>
        </Box>
      </Box>
    );
  }

  const youtubeEmbedUrl = getYouTubeEmbedUrl(project.video_url ?? '');
  const hasDemoVideo = Boolean(youtubeEmbedUrl);
  const displayTags = project.tags;

  return (
    <Box minH="100vh" bg="gray.50">
      <Navbar />
      <Box
        px={{ base: '20px', md: '32px' }}
        pt="32px"
        pb="64px"
        maxW="1200px"
        mx="auto"
        w="100%"
      >
        <Box
          bg="gray.100"
          borderRadius="16px"
          border="1px solid"
          borderColor="gray.200"
          overflow="hidden"
        >
          <Box
            px={{ base: '20px', md: '28px' }}
            pt={{ base: '20px', md: '28px' }}
            pb={{ base: '20px', md: '26px' }}
          >
            <Flex align="flex-start" justify="space-between" gap="24px">
              <HStack align="flex-start" gap="20px" flex="1" minW={0}>
                <Box
                  w={{ base: '104px', md: '128px' }}
                  h={{ base: '104px', md: '128px' }}
                  borderRadius="12px"
                  overflow="hidden"
                  flexShrink={0}
                >
                  <ProjectLogoPlaceholder />
                </Box>

                <VStack align="start" gap="12px" flex="1" minW={0}>
                  <HStack gap="10px" align="center" flexWrap="wrap">
                    <Text
                      fontSize={{ base: 'xl', md: '2xl' }}
                      fontWeight="bold"
                      color="gray.900"
                      lineHeight={{ base: '34px', md: '40px' }}
                      lineClamp={2}
                    >
                      {project.title}
                    </Text>
                    {canSeePublishStateBadge && (
                      <HStack
                        gap="6px"
                        bg={project.is_published ? 'green.500' : 'yellow.200'}
                        color={project.is_published ? 'white' : 'yellow.900'}
                        border="1px solid"
                        borderColor={
                          project.is_published ? 'green.500' : 'yellow.400'
                        }
                        borderRadius="full"
                        px="12px"
                        py="5px"
                      >
                        <Text
                          fontSize="sm"
                          lineHeight="18px"
                          fontWeight="semibold"
                          whiteSpace="nowrap"
                        >
                          {project.is_published ? 'Published' : 'Draft'}
                        </Text>
                      </HStack>
                    )}
                  </HStack>

                  <Text
                    fontSize="md"
                    color="gray.600"
                    lineHeight="26px"
                    maxW="760px"
                    lineClamp={2}
                  >
                    {project.short_description}
                  </Text>

                  {displayTags.length > 0 && (
                    <Wrap gap="10px">
                      {displayTags.map((tag) => (
                        <Badge
                          key={tag.id}
                          bg="white"
                          border="1px solid"
                          borderColor="orange.200"
                          color="gray.700"
                          borderRadius="10px"
                          px="14px"
                          py="7px"
                          fontSize="sm"
                          fontWeight="medium"
                          textTransform="none"
                        >
                          {tag.name}
                        </Badge>
                      ))}
                    </Wrap>
                  )}

                  <HStack gap="12px" pt="4px" flexWrap="wrap">
                    {project.demo_url?.trim() ? (
                      <ChakraLink
                        href={project.demo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        _hover={{ textDecoration: 'none' }}
                      >
                        <Button
                          bg="orange.400"
                          color="white"
                          borderRadius="12px"
                          h="44px"
                          px="18px"
                          fontSize="md"
                          fontWeight="semibold"
                          _hover={{ bg: 'orange.500' }}
                        >
                          <HStack gap="8px">
                            <LuExternalLink size={16} />
                            <Text>Visit Website</Text>
                          </HStack>
                        </Button>
                      </ChakraLink>
                    ) : null}

                    {project.github_url?.trim() ? (
                      <ChakraLink
                        href={project.github_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        _hover={{ textDecoration: 'none' }}
                      >
                        <Button
                          bg="white"
                          color="gray.800"
                          borderRadius="12px"
                          h="44px"
                          px="18px"
                          fontSize="md"
                          fontWeight="semibold"
                          border="1px solid"
                          borderColor="gray.300"
                          _hover={{ bg: 'gray.50' }}
                        >
                          <HStack gap="8px">
                            <LuGithub size={16} />
                            <Text>GitHub</Text>
                          </HStack>
                        </Button>
                      </ChakraLink>
                    ) : null}

                    {isOwner && (
                      <Button
                        type="button"
                        bg="orange.50"
                        color="orange.800"
                        borderRadius="12px"
                        h="44px"
                        px="18px"
                        fontSize="md"
                        fontWeight="semibold"
                        _hover={{ bg: 'orange.100' }}
                        boxShadow="inset 0 0 0 1px rgba(251,146,60,0.10)"
                        onClick={() =>
                          router.push(projectEditPath(project.slug))
                        }
                      >
                        <HStack gap="8px">
                          <LuPencil size={16} />
                          <Text>Edit Project</Text>
                        </HStack>
                      </Button>
                    )}
                  </HStack>
                </VStack>
              </HStack>

              <Box pt="4px" flexShrink={0}>
                <UpvoteBox
                  projectId={project.id}
                  votes={project.vote_count}
                  viewerHasVoted={project.viewer_has_voted}
                />
              </Box>
            </Flex>

            <Box h="1px" bg="gray.200" my="22px" />

            <VStack align="stretch" gap="16px">
              <Box overflowX="auto" overflowY="hidden" pb="2px">
                <HStack gap="20px" align="stretch" minW="max-content">
                  {projectCreator && (
                    <MemberMetaBlock
                      username={projectCreator.username}
                      fullName={projectCreator.full_name}
                      profilePictureUrl={projectCreator.profile_picture_url}
                      description="Project Creator"
                      onClick={() =>
                        router.push(profilePath(projectCreator.username))
                      }
                    />
                  )}
                  {nonOwnerMembers.map((member) => (
                    <MemberMetaBlock
                      key={member.user_id}
                      username={member.username}
                      fullName={member.full_name}
                      profilePictureUrl={member.profile_picture_url}
                      description="Team Member"
                      onClick={() => router.push(profilePath(member.username))}
                    />
                  ))}
                </HStack>
              </Box>
            </VStack>
          </Box>
        </Box>

        <Box
          mt="26px"
          bg="gray.100"
          borderRadius="16px"
          border="1px solid"
          borderColor="gray.200"
          overflow="hidden"
        >
          <Box
            px={{ base: '18px', md: '24px' }}
            py={{ base: '22px', md: '28px' }}
          >
            <HStack mb="14px" gap="10px" align="center">
              <Box color="gray.800">
                <LuFileText size={22} />
              </Box>
              <Text
                fontSize="2xl"
                fontWeight="bold"
                color="gray.900"
                lineHeight="34px"
              >
                About This Project
              </Text>
            </HStack>
            <Text
              fontSize="md"
              color="gray.700"
              lineHeight="28px"
              whiteSpace="pre-wrap"
            >
              {project.long_description?.trim() ||
                'No extended project description has been added yet.'}
            </Text>
          </Box>
        </Box>

        <Box
          mt="26px"
          bg="gray.100"
          borderRadius="16px"
          border="1px solid"
          borderColor="gray.200"
          overflow="hidden"
        >
          <Box
            px={{ base: '18px', md: '24px' }}
            py={{ base: '22px', md: '28px' }}
          >
            <HStack mb="14px" gap="10px" align="center">
              <Box color="gray.800">
                <LuVideo size={22} />
              </Box>
              <Text
                fontSize="2xl"
                fontWeight="bold"
                color="gray.900"
                lineHeight="34px"
              >
                Project Video
              </Text>
            </HStack>

            {hasDemoVideo ? (
              <Box
                borderRadius="14px"
                overflow="hidden"
                border="1px solid"
                borderColor="gray.300"
                bg="black"
              >
                <iframe
                  src={youtubeEmbedUrl ?? undefined}
                  title={`${project.title} demo video`}
                  style={{
                    width: '100%',
                    aspectRatio: '16 / 9',
                    display: 'block',
                    border: 0,
                  }}
                  loading="lazy"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              </Box>
            ) : (
              <Box
                position="relative"
                aspectRatio="16 / 9"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="14px"
                bg="#1f1f1f"
                overflow="hidden"
                w="100%"
              >
                <Box
                  position="absolute"
                  inset={0}
                  bg="linear-gradient(180deg, rgba(255,255,255,0.03), transparent 28%)"
                  pointerEvents="none"
                />
                <Box
                  position="absolute"
                  inset={0}
                  bg="radial-gradient(circle at center, rgba(255,255,255,0.03), transparent 42%)"
                  pointerEvents="none"
                />

                <Flex
                  position="absolute"
                  insetX={0}
                  top="0"
                  bottom="70px"
                  align="center"
                  justify="center"
                  zIndex={1}
                  direction="column"
                  gap="14px"
                >
                  <Flex
                    w={{ base: '88px', md: '104px' }}
                    h={{ base: '88px', md: '104px' }}
                    borderRadius="full"
                    align="center"
                    justify="center"
                    bg="rgba(28, 28, 28, 0.74)"
                    border="4px solid"
                    borderColor="whiteAlpha.300"
                    boxShadow="0 20px 60px rgba(0,0,0,0.3)"
                  >
                    <Box color="white" ml="5px">
                      <LuPlay size={42} fill="currentColor" />
                    </Box>
                  </Flex>
                  <Text
                    fontSize={{ base: 'sm', md: 'md' }}
                    fontWeight="medium"
                    color="whiteAlpha.900"
                    textAlign="center"
                    px="20px"
                  >
                    No video has been added yet.
                  </Text>
                </Flex>

                <Box
                  position="absolute"
                  left="0"
                  right="0"
                  bottom="0"
                  zIndex={1}
                  bg="rgba(12, 12, 12, 0.96)"
                  borderTop="1px solid"
                  borderColor="whiteAlpha.100"
                  px={{ base: '14px', md: '18px' }}
                  py={{ base: '10px', md: '12px' }}
                >
                  <VStack align="stretch" gap="10px">
                    <Box
                      w="100%"
                      h="4px"
                      borderRadius="full"
                      bg="whiteAlpha.300"
                      overflow="hidden"
                    >
                      <Box
                        w={project.video_url?.trim() ? '36%' : '0%'}
                        h="100%"
                        borderRadius="full"
                        bg="rgba(239, 68, 68, 0.95)"
                      />
                      <Box
                        position="relative"
                        top="-6px"
                        left={project.video_url?.trim() ? '36%' : '0%'}
                        transform="translateX(-50%)"
                        w="14px"
                        h="14px"
                        borderRadius="full"
                        bg="white"
                        border="2px solid"
                        borderColor="rgba(239, 68, 68, 0.95)"
                      />
                    </Box>

                    <HStack justify="space-between" gap="12px" align="center">
                      <HStack gap={{ base: '10px', md: '12px' }} color="white">
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuPlay size={18} fill="currentColor" />
                        </Box>
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuSkipBack size={18} />
                        </Box>
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuSkipForward size={18} />
                        </Box>
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuVolume2 size={18} />
                        </Box>
                        <Box
                          display={{ base: 'none', md: 'block' }}
                          w="140px"
                          h="3px"
                          borderRadius="full"
                          bg="whiteAlpha.400"
                          overflow="hidden"
                          ml="4px"
                        >
                          <Box w="46%" h="100%" bg="whiteAlpha.900" />
                        </Box>
                      </HStack>

                      <HStack gap={{ base: '12px', md: '14px' }} color="white">
                        <Text
                          fontSize={{ base: 'xs', md: 'sm' }}
                          fontWeight="semibold"
                          letterSpacing="0.02em"
                          color="whiteAlpha.900"
                        >
                          00:00 / 10:00
                        </Text>
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuSettings2 size={18} />
                        </Box>
                        <Box display="flex" alignItems="center" justifyContent="center">
                          <LuExpand size={18} />
                        </Box>
                      </HStack>
                    </HStack>
                  </VStack>
                </Box>
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
