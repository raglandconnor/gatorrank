'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  Avatar,
  Link as ChakraLink,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LuGlobe,
  LuGithub,
  LuVideo,
  LuTrophy,
  LuExternalLink,
  LuPencil,
  LuChevronUp,
} from 'react-icons/lu';
import { Navbar } from '@/components/Navbar';
import { getProjectDetailById } from '@/data/mock-project';
import { mockProfile } from '@/data/mock-profile';
import { RoleBadge } from '@/components/ui/rolebadge';

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

    // YouTube video ids are 11 chars using base64url charset: [A-Za-z0-9_-]
    const VIDEO_ID_REGEX = /^[a-zA-Z0-9_-]{11}$/;
    if (!videoId) return null;
    const normalizedVideoId = videoId.trim();
    if (!VIDEO_ID_REGEX.test(normalizedVideoId)) return null;

    return `https://www.youtube.com/embed/${encodeURIComponent(
      normalizedVideoId,
    )}`;
  } catch {
    return null;
  }
}

function UpvoteBox({ votes }: { votes: number }) {
  const [isVoted, setIsVoted] = useState(false);
  const voteCount = votes + (isVoted ? 1 : 0);

  return (
    <motion.div
      whileTap={{ scale: 1.2, y: -3 }}
      style={{ display: 'contents' }}
    >
      <Button
        type="button"
        variant="plain"
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        p="0"
        gap="8px"
        w="108px"
        minW="108px"
        h="108px"
        overflow="hidden"
        bg={isVoted ? 'orange.50' : 'white'}
        border="2px solid"
        borderColor={isVoted ? 'orange.400' : 'orange.200'}
        borderRadius="12px"
        cursor="pointer"
        userSelect="none"
        _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
        _focusVisible={{
          borderColor: 'orange.400',
          boxShadow: '0 0 0 3px rgba(251,146,60,0.35)',
        }}
        transition="background 0.15s, border-color 0.15s, box-shadow 0.15s"
        onClick={() => setIsVoted((v) => !v)}
        aria-label="Upvote"
        aria-pressed={isVoted}
      >
        <Box color={isVoted ? 'orange.500' : 'gray.800'}>
          <LuChevronUp size={24} />
        </Box>
        <Box position="relative" h="24px" w="100%" overflow="hidden">
          <AnimatePresence mode="sync" initial={false}>
            <motion.span
              key={voteCount}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -10, opacity: 0 }}
              transition={{ duration: 0.15 }}
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                fontWeight: 700,
                lineHeight: '24px',
                color: isVoted ? 'rgb(234,88,12)' : 'rgb(17,24,39)',
              }}
            >
              {voteCount}
            </motion.span>
          </AnimatePresence>
        </Box>
        <Text
          fontSize="xs"
          letterSpacing="0.08em"
          color={isVoted ? 'orange.600' : 'gray.600'}
          lineHeight="14px"
        >
          UPVOTE
        </Text>
      </Button>
    </motion.div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;
  const project = getProjectDetailById(projectId);

  if (!project) {
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
              Project not found
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

  const hasLinks =
    Boolean(project.websiteUrl?.trim()) || Boolean(project.githubUrl?.trim());
  const youtubeEmbedUrl = getYouTubeEmbedUrl(project.demoVideoUrl ?? '');
  const hasDemoVideo = Boolean(youtubeEmbedUrl);

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
        {/* Top project card */}
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
              {/* Left content */}
              <HStack align="flex-start" gap="20px" flex="1" minW={0}>
                <Box
                  w={{ base: '104px', md: '128px' }}
                  h={{ base: '104px', md: '128px' }}
                  borderRadius="12px"
                  overflow="hidden"
                  bg="gray.200"
                  flexShrink={0}
                >
                  {project.imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={project.imageUrl}
                      alt={project.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        display: 'block',
                      }}
                    />
                  ) : null}
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
                      {project.name}
                    </Text>
                    <HStack
                      gap="6px"
                      bg="orange.400"
                      color="white"
                      borderRadius="full"
                      px="12px"
                      py="5px"
                    >
                      <LuTrophy size={16} />
                      <Text
                        fontSize="sm"
                        lineHeight="18px"
                        fontWeight="semibold"
                        whiteSpace="nowrap"
                      >
                        #1 Trending Project This Month
                      </Text>
                    </HStack>
                  </HStack>

                  <Text
                    fontSize="md"
                    color="gray.600"
                    lineHeight="26px"
                    maxW="760px"
                    lineClamp={2}
                  >
                    {project.shortDescription}
                  </Text>

                  {/* Tags */}
                  {project.tags.length > 0 ? (
                    <Wrap gap="10px">
                      {project.tags.map((tag) => (
                        <Box
                          key={tag}
                          bg="white"
                          border="1px solid"
                          borderColor="orange.200"
                          borderRadius="10px"
                          px="14px"
                          py="7px"
                        >
                          <Text
                            fontSize="sm"
                            color="gray.700"
                            lineHeight="20px"
                          >
                            {tag}
                          </Text>
                        </Box>
                      ))}
                    </Wrap>
                  ) : null}

                  {/* Actions */}
                  <HStack gap="12px" pt="4px" flexWrap="wrap">
                    {project.websiteUrl?.trim() ? (
                      <ChakraLink
                        href={project.websiteUrl}
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
                    ) : (
                      <Button
                        bg="orange.400"
                        color="white"
                        borderRadius="12px"
                        h="44px"
                        px="18px"
                        fontSize="md"
                        fontWeight="semibold"
                        opacity={0.6}
                        cursor="not-allowed"
                        _hover={{ bg: 'orange.400' }}
                        disabled
                      >
                        <HStack gap="8px">
                          <LuExternalLink size={16} />
                          <Text>Visit Website</Text>
                        </HStack>
                      </Button>
                    )}

                    <Button
                      type="button"
                      variant="outline"
                      border="1px solid"
                      borderColor="gray.300"
                      bg="white"
                      borderRadius="12px"
                      h="44px"
                      px="18px"
                      fontSize="md"
                      color="gray.800"
                      _hover={{ bg: 'gray.50' }}
                      onClick={() => router.push('/projects/edit')}
                    >
                      <HStack gap="8px">
                        <LuPencil size={16} />
                        <Text>Edit Project</Text>
                      </HStack>
                    </Button>
                  </HStack>
                </VStack>
              </HStack>

              {/* Right upvote */}
              <Box pt="4px" flexShrink={0}>
                <UpvoteBox votes={project.votes} />
              </Box>
            </Flex>

            {/* Divider */}
            <Box h="1px" bg="gray.200" my="22px" />

            {/* Creator row */}
            <HStack justify="space-between" flexWrap="wrap" gap="16px">
              <HStack gap="14px">
                <Avatar.Root
                  w="52px"
                  h="52px"
                  borderRadius="full"
                  overflow="hidden"
                >
                  <Avatar.Fallback
                    name={mockProfile.name}
                    bg="gray.300"
                    color="gray.700"
                    fontSize="md"
                    fontWeight="bold"
                  />
                  {mockProfile.avatarUrl && (
                    <Avatar.Image src={mockProfile.avatarUrl} />
                  )}
                </Avatar.Root>

                <VStack align="start" gap="2px">
                  <HStack gap="8px" flexWrap="wrap">
                    <Text
                      fontSize="md"
                      fontWeight="bold"
                      color="gray.900"
                      lineHeight="22px"
                    >
                      {mockProfile.name}
                    </Text>
                    <RoleBadge role={mockProfile.role} />
                  </HStack>
                  <Text fontSize="sm" color="gray.600" lineHeight="18px">
                    Project Creator
                  </Text>
                </VStack>
              </HStack>

              {/* Optional links (small, like design usually keeps them minimal) */}
              {hasLinks ? (
                <HStack gap="16px" flexWrap="wrap">
                  {project.websiteUrl?.trim() ? (
                    <ChakraLink
                      href={project.websiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      display="inline-flex"
                      alignItems="center"
                      gap="6px"
                      fontSize="md"
                      color="gray.700"
                      _hover={{
                        color: 'gray.900',
                        textDecoration: 'underline',
                      }}
                    >
                      <LuGlobe size={16} />
                      Website
                    </ChakraLink>
                  ) : null}
                  {project.githubUrl?.trim() ? (
                    <ChakraLink
                      href={project.githubUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      display="inline-flex"
                      alignItems="center"
                      gap="6px"
                      fontSize="md"
                      color="gray.700"
                      _hover={{
                        color: 'gray.900',
                        textDecoration: 'underline',
                      }}
                    >
                      <LuGithub size={16} />
                      GitHub
                    </ChakraLink>
                  ) : null}
                </HStack>
              ) : null}
            </HStack>
          </Box>
        </Box>

        {/* About card */}
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
            <Text
              fontSize="2xl"
              fontWeight="bold"
              color="gray.900"
              lineHeight="34px"
              mb="14px"
            >
              About This Project
            </Text>
            <Text
              fontSize="md"
              color="gray.700"
              lineHeight="28px"
              whiteSpace="pre-wrap"
            >
              {project.fullDescription}
            </Text>
          </Box>
        </Box>

        {/* Project Video card */}
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
                  title={`${project.name} demo video`}
                  style={{
                    width: '100%',
                    aspectRatio: '16 / 9',
                    display: 'block',
                    border: 0,
                  }}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              </Box>
            ) : (
              <Flex
                direction="column"
                align="center"
                justify="center"
                gap="12px"
                minH={{ base: '180px', md: '220px' }}
                border="1px dashed"
                borderColor="gray.300"
                borderRadius="14px"
                bg="white"
                px="20px"
                py="24px"
                textAlign="center"
              >
                <Text fontSize="md" color="gray.700">
                  {project.demoVideoUrl?.trim()
                    ? 'Video link is not a valid YouTube URL.'
                    : 'No project video yet.'}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Add a YouTube link from the edit page to embed it here.
                </Text>
                <Button
                  type="button"
                  bg="orange.400"
                  color="white"
                  borderRadius="12px"
                  h="42px"
                  px="18px"
                  fontSize="sm"
                  _hover={{ bg: 'orange.500' }}
                  onClick={() => router.push('/projects/edit')}
                >
                  Add Video
                </Button>
              </Flex>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
