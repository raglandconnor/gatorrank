'use client';

import NextLink from 'next/link';
import { useEffect, useState, type MouseEvent } from 'react';
import {
  Box,
  Badge,
  HStack,
  VStack,
  Text,
  Flex,
  SimpleGrid,
  LinkBox,
  LinkOverlay,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import { LuMessageSquare, LuChevronUp, LuArrowRight } from 'react-icons/lu';
import { getMyProjects, getUserProjectsByUsername } from '@/lib/api/users';
import type { ProjectListItem } from '@/lib/api/types/project';
import { useProjectVote } from '@/hooks/useProjectVote';
import { projectPath } from '@/lib/routes';
import { ProjectLogoPlaceholder } from '@/components/projects/ProjectLogoPlaceholder';
import { ProjectCollectionLoading } from '@/components/projects/ProjectCollectionLoading';

function CommentPill({
  count,
  onClick,
}: {
  count: number;
  onClick?: (event: MouseEvent<HTMLElement>) => void;
}) {
  return (
    <Box
      data-project-card-action="true"
      as="button"
      display="flex"
      alignItems="center"
      justifyContent="center"
      gap="7px"
      bg="white"
      border="1.6px solid"
      borderColor="orange.200"
      borderRadius="12px"
      pl="13px"
      pr="10px"
      h="42px"
      minW="76px"
      cursor="pointer"
      _hover={{ bg: 'orange.50' }}
      transition="background 0.15s, border-color 0.15s"
      onClick={onClick}
    >
      <Flex
        w="15px"
        minW="15px"
        h="15px"
        align="center"
        justify="center"
        color="gray.700"
      >
        <LuMessageSquare size={15} />
      </Flex>
      <Flex w="18px" minW="18px" align="center" justify="center">
        <Text
          fontSize="sm"
          fontWeight="normal"
          color="gray.700"
          lineHeight="20px"
        >
          {count}
        </Text>
      </Flex>
    </Box>
  );
}

function VotePill({
  count,
  active = false,
  pending = false,
  onClick,
}: {
  count: number;
  active?: boolean;
  pending?: boolean;
  onClick?: (event: MouseEvent<HTMLElement>) => void;
}) {
  return (
    <Box
      data-project-card-action="true"
      as="button"
      display="flex"
      alignItems="center"
      justifyContent="center"
      gap="2px"
      bg={active ? 'orange.50' : 'white'}
      border="1.6px solid"
      borderColor={active ? 'orange.400' : 'orange.200'}
      borderRadius="12px"
      pl="12px"
      pr="5px"
      h="42px"
      minW="76px"
      cursor={pending ? 'wait' : 'pointer'}
      opacity={pending ? 0.85 : 1}
      _hover={{ bg: active ? 'orange.100' : 'orange.50' }}
      transition="background 0.15s, border-color 0.15s, opacity 0.15s"
      onClick={onClick}
      aria-disabled={pending}
    >
      <Flex
        w="14px"
        minW="14px"
        h="14px"
        align="center"
        justify="center"
        color={active ? 'orange.500' : 'gray.700'}
      >
        <LuChevronUp size={15} />
      </Flex>
      <Box position="relative" h="20px" w="28px" overflow="hidden">
        <AnimatePresence mode="sync" initial={false}>
          <motion.span
            key={count}
            initial={{ y: 8, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -8, opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.875rem',
              fontWeight: 400,
              lineHeight: '20px',
              color: active ? 'rgb(234,88,12)' : 'rgb(55,65,81)',
            }}
          >
            {count}
          </motion.span>
        </AnimatePresence>
      </Box>
    </Box>
  );
}

function UserProjectCard({ project }: { project: ProjectListItem }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const { isVoted, voteCount, isPending, toggleVote } = useProjectVote({
    projectId: project.id,
    initialVoteCount: project.vote_count,
    initialViewerHasVoted: project.viewer_has_voted,
  });
  const backgroundColor = project.is_published
    ? isPressed
      ? '#e6e6e6'
      : isHovered
        ? '#efefef'
        : 'gray.100'
    : isPressed
      ? '#ffe8a3'
      : isHovered
        ? '#fff0bf'
        : '#fff7db';

  return (
    <LinkBox
      position="relative"
      bg={backgroundColor}
      borderRadius="13px"
      p="16px"
      w="100%"
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setIsPressed(false);
      }}
      onPointerDownCapture={(event) => {
        const target = event.target as HTMLElement | null;
        if (target?.closest('[data-project-card-action="true"]')) return;
        setIsPressed(true);
      }}
      onPointerUpCapture={() => setIsPressed(false)}
      onPointerCancel={() => setIsPressed(false)}
      _focusWithin={{
        boxShadow: '0 0 0 3px rgba(148,163,184,0.12)',
      }}
    >
      <VStack align="start" gap="12px" w="100%">
        <Box
          w="100%"
          h="144px"
          borderRadius="10px"
          overflow="hidden"
          flexShrink={0}
        >
          <ProjectLogoPlaceholder compact />
        </Box>

        <VStack align="start" gap="10px" w="100%">
          <HStack gap="8px" align="center" flexWrap="wrap">
            <LinkOverlay
              as={NextLink}
              href={projectPath(project.slug)}
              data-project-card-link="true"
              _hover={{ textDecoration: 'none' }}
              _focusVisible={{ textDecoration: 'none' }}
            >
              <Text
                fontSize="md"
                fontWeight="bold"
                color={isHovered ? 'orange.600' : 'gray.900'}
                lineHeight="24px"
                transition="color 0.15s"
                overflow="hidden"
                textOverflow="ellipsis"
                whiteSpace="nowrap"
              >
                {project.title}
              </Text>
            </LinkOverlay>
            {!project.is_published && (
              <Badge
                bg="yellow.200"
                color="yellow.900"
                borderRadius="full"
                px="8px"
                py="3px"
                fontSize="10px"
                fontWeight="bold"
                textTransform="uppercase"
                letterSpacing="0.04em"
              >
                Draft
              </Badge>
            )}
            <Box
              color="orange.600"
              opacity={isHovered ? 1 : 0}
              transition="opacity 0.15s"
              flexShrink={0}
            >
              <LuArrowRight size={13} />
            </Box>
          </HStack>

          <Text
            position="relative"
            zIndex={1}
            fontSize="sm"
            color="gray.600"
            lineHeight="22px"
            lineClamp={2}
            minH="44px"
          >
            {project.short_description}
          </Text>

          <HStack gap="8px" mt="2px" position="relative" zIndex={1}>
            <motion.div
              whileTap={{ scale: 1.06 }}
              style={{ display: 'contents' }}
            >
              <CommentPill
                count={0}
                onClick={(event) => event.stopPropagation()}
              />
            </motion.div>

            <motion.div
              whileTap={{ scale: 1.2, y: -3 }}
              style={{ display: 'contents' }}
            >
              <VotePill
                count={voteCount}
                active={isVoted}
                pending={isPending}
                onClick={(event) => {
                  event.stopPropagation();
                  void toggleVote();
                }}
              />
            </motion.div>
          </HStack>
        </VStack>
      </VStack>
    </LinkBox>
  );
}

interface ProfileUserProjectsProps {
  username: string;
  isOwn: boolean;
  onLoadComplete?: (count: number) => void;
}

export function ProfileUserProjects({
  username,
  isOwn,
  onLoadComplete,
}: ProfileUserProjectsProps) {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = isOwn
          ? await getMyProjects({ limit: 20, sort: 'new', visibility: 'all' })
          : await getUserProjectsByUsername(username);
        setProjects(data.items);
        onLoadComplete?.(data.items.length);
      } catch {
        setError('Could not load projects.');
        onLoadComplete?.(-1);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [isOwn, username, onLoadComplete]);

  return (
    <VStack align="start" gap="16px" w="100%">
      <Text fontSize="md" fontWeight="bold" color="gray.900" lineHeight="30px">
        Projects
      </Text>

      {loading && <ProjectCollectionLoading variant="grid" count={3} />}

      {!loading && error && (
        <Text fontSize="sm" color="red.500">
          {error}
        </Text>
      )}

      {!loading && !error && projects.length === 0 && isOwn && (
        <VStack align="stretch" gap="14px" w="100%">
          <Text fontSize="sm" color="gray.500" lineHeight="24px">
            Your projects will show up here once you publish or save your first
            draft.
          </Text>
          <ProjectCollectionLoading
            variant="grid"
            count={3}
            showMessage={false}
          />
        </VStack>
      )}

      {!loading && !error && projects.length === 0 && !isOwn && (
        <Text fontSize="sm" color="gray.400" lineHeight="24px">
          No projects shared yet.
        </Text>
      )}

      {!loading && !error && projects.length > 0 && (
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap="16px" w="100%">
          {projects.map((project) => (
            <UserProjectCard key={project.id} project={project} />
          ))}
        </SimpleGrid>
      )}
    </VStack>
  );
}
