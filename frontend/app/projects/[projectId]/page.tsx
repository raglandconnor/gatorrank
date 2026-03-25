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
  LuArrowLeft,
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

function UpvoteBox({ votes }: { votes: number }) {
  const [isVoted, setIsVoted] = useState(false);
  const voteCount = votes + (isVoted ? 1 : 0);

  return (
    <motion.div
      whileTap={{ scale: 1.2, y: -3 }}
      style={{ display: 'contents' }}
    >
      <Flex
        direction="column"
        align="center"
        justify="center"
        gap="6px"
        w="92px"
        minW="92px"
        h="92px"
        overflow="hidden"
        bg={isVoted ? 'orange.50' : 'white'}
        border="2px solid"
        borderColor={isVoted ? 'orange.400' : 'orange.200'}
        borderRadius="12px"
        cursor="pointer"
        userSelect="none"
        _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
        transition="background 0.15s, border-color 0.15s"
        onClick={() => setIsVoted((v) => !v)}
        aria-label="Upvote"
        role="button"
      >
        <Box color={isVoted ? 'orange.500' : 'gray.800'}>
          <LuChevronUp size={20} />
        </Box>
        <Box position="relative" h="22px" w="100%" overflow="hidden">
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
                fontSize: '1.05rem',
                fontWeight: 700,
                lineHeight: '22px',
                color: isVoted ? 'rgb(234,88,12)' : 'rgb(17,24,39)',
              }}
            >
              {voteCount}
            </motion.span>
          </AnimatePresence>
        </Box>
        <Text
          fontSize="2xs"
          letterSpacing="0.08em"
          color={isVoted ? 'orange.600' : 'gray.600'}
          lineHeight="14px"
        >
          UPVOTE
        </Text>
      </Flex>
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
    Boolean(project.websiteUrl?.trim()) ||
    Boolean(project.githubUrl?.trim()) ||
    Boolean(project.demoVideoUrl?.trim());

  return (
    <Box minH="100vh" bg="gray.50">
      <Navbar />
      <Box px="36px" pt="32px" pb="64px" maxW="1120px" mx="auto" w="100%">
        {/* Top project card */}
        <Box
          bg="gray.100"
          borderRadius="16px"
          border="1px solid"
          borderColor="gray.200"
          overflow="hidden"
        >
          <Box
            px={{ base: '18px', md: '24px' }}
            pt={{ base: '18px', md: '22px' }}
            pb={{ base: '18px', md: '22px' }}
          >
            {/* Back row (dedicated) */}
            <HStack justify="flex-start" mb="14px">
              <Button
                type="button"
                variant="ghost"
                color="gray.700"
                h="36px"
                px="10px"
                borderRadius="12px"
                _hover={{ bg: 'gray.200' }}
                onClick={() => router.push('/profile')}
              >
                <HStack gap="8px">
                  <LuArrowLeft size={16} />
                  <Text>Back</Text>
                </HStack>
              </Button>
            </HStack>

            <Flex align="flex-start" justify="space-between" gap="18px">
              {/* Left content */}
              <HStack align="flex-start" gap="16px" flex="1" minW={0}>
                <Box
                  w="64px"
                  h="64px"
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

                <VStack align="start" gap="10px" flex="1" minW={0}>
                  <HStack gap="10px" align="center" flexWrap="wrap">
                    <Text
                      fontSize={{ base: 'lg', md: 'xl' }}
                      fontWeight="bold"
                      color="gray.900"
                      lineHeight="28px"
                      lineClamp={2}
                    >
                      {project.name}
                    </Text>
                    <HStack
                      gap="6px"
                      bg="orange.400"
                      color="white"
                      borderRadius="full"
                      px="10px"
                      py="4px"
                    >
                      <LuTrophy size={14} />
                      <Text
                        fontSize="xs"
                        lineHeight="16px"
                        fontWeight="semibold"
                        whiteSpace="nowrap"
                      >
                        #1 Trending Project This Month
                      </Text>
                    </HStack>
                  </HStack>

                  <Text
                    fontSize="sm"
                    color="gray.600"
                    lineHeight="22px"
                    maxW="640px"
                    lineClamp={2}
                  >
                    {project.shortDescription}
                  </Text>

                  {/* Tags */}
                  {project.tags.length > 0 ? (
                    <Wrap gap="8px">
                      {project.tags.map((tag) => (
                        <Box
                          key={tag}
                          bg="white"
                          border="1px solid"
                          borderColor="orange.200"
                          borderRadius="10px"
                          px="12px"
                          py="6px"
                        >
                          <Text
                            fontSize="xs"
                            color="gray.700"
                            lineHeight="18px"
                          >
                            {tag}
                          </Text>
                        </Box>
                      ))}
                    </Wrap>
                  ) : null}

                  {/* Actions */}
                  <HStack gap="10px" pt="2px" flexWrap="wrap">
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
                          h="40px"
                          px="16px"
                          fontSize="sm"
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
                        h="40px"
                        px="16px"
                        fontSize="sm"
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
                      h="40px"
                      px="16px"
                      fontSize="sm"
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
              <Box pt="2px" flexShrink={0}>
                <UpvoteBox votes={project.votes} />
              </Box>
            </Flex>

            {/* Divider */}
            <Box h="1px" bg="gray.200" my="18px" />

            {/* Creator row */}
            <HStack justify="space-between" flexWrap="wrap" gap="12px">
              <HStack gap="12px">
                <Avatar.Root
                  w="44px"
                  h="44px"
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
                      fontSize="sm"
                      fontWeight="bold"
                      color="gray.900"
                      lineHeight="20px"
                    >
                      {mockProfile.name}
                    </Text>
                    <RoleBadge role={mockProfile.role} />
                  </HStack>
                  <Text fontSize="xs" color="gray.600" lineHeight="16px">
                    Project Creator
                  </Text>
                </VStack>
              </HStack>

              {/* Optional links (small, like design usually keeps them minimal) */}
              {hasLinks ? (
                <HStack gap="14px" flexWrap="wrap">
                  {project.websiteUrl?.trim() ? (
                    <ChakraLink
                      href={project.websiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      display="inline-flex"
                      alignItems="center"
                      gap="6px"
                      fontSize="sm"
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
                      fontSize="sm"
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
                  {project.demoVideoUrl?.trim() ? (
                    <ChakraLink
                      href={project.demoVideoUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      display="inline-flex"
                      alignItems="center"
                      gap="6px"
                      fontSize="sm"
                      color="gray.700"
                      _hover={{
                        color: 'gray.900',
                        textDecoration: 'underline',
                      }}
                    >
                      <LuVideo size={16} />
                      Demo video
                    </ChakraLink>
                  ) : null}
                </HStack>
              ) : null}
            </HStack>
          </Box>
        </Box>

        {/* About card */}
        <Box
          mt="22px"
          bg="gray.100"
          borderRadius="16px"
          border="1px solid"
          borderColor="gray.200"
          overflow="hidden"
        >
          <Box
            px={{ base: '18px', md: '24px' }}
            py={{ base: '18px', md: '22px' }}
          >
            <Text
              fontSize="lg"
              fontWeight="bold"
              color="gray.900"
              lineHeight="28px"
              mb="10px"
            >
              About This Project
            </Text>
            <Text
              fontSize="sm"
              color="gray.700"
              lineHeight="24px"
              whiteSpace="pre-wrap"
            >
              {project.fullDescription}
            </Text>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
