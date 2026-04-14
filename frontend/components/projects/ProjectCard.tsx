'use client';

import NextLink from 'next/link';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  HStack,
  VStack,
  Text,
  LinkBox,
  LinkOverlay,
  Button,
} from '@chakra-ui/react';
import { LuMessageSquare, LuChevronUp, LuArrowRight } from 'react-icons/lu';
import type { Project } from '@/types/project';
import { useProjectVote } from '@/hooks/useProjectVote';
import { projectPath } from '@/lib/routes';
import { ProjectInlineTags } from '@/components/projects/ProjectInlineTags';

interface ProjectCardProps {
  project: Project;
  rank: number;
}

export function ProjectCard({ project, rank }: ProjectCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const { isVoted, voteCount, toggleVote } = useProjectVote({
    projectId: String(project.id),
    initialVoteCount: project.votes,
    initialViewerHasVoted: project.viewerHasVoted ?? false,
  });

  const backgroundColor = isPressed
    ? '#e6e6e6'
    : isHovered
      ? '#efefef'
      : 'gray.100';

  return (
    <LinkBox
      bg={backgroundColor}
      borderRadius="13px"
      px="20px"
      py="9px"
      gap="20px"
      alignItems="flex-start"
      display="flex"
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
      <Box w="60px" h="60px" bg="gray.300" borderRadius="13px" flexShrink={0} />

      <VStack align="start" gap="6px" flex={1} minW={0}>
        <VStack align="start" gap="6px" minH="60px" justify="center" w="100%">
          <HStack gap="6px" align="center" display="inline-flex" minW={0}>
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
                lineHeight="30px"
                transition="color 0.15s"
                lineClamp={1}
              >
                {rank}. {project.name}
              </Text>
            </LinkOverlay>
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
            fontSize="sm"
            color="gray.800"
            lineHeight="24px"
            lineClamp={1}
            w="100%"
          >
            {project.description}
          </Text>
        </VStack>

        <ProjectInlineTags tags={project.tags} maxRows={1} />
      </VStack>

      <HStack gap={{ base: '10px', md: '18px' }} pt="6px" flexShrink={0}>
        <motion.div whileTap={{ scale: 1.1 }} style={{ display: 'contents' }}>
          <Button
            data-project-card-action="true"
            type="button"
            variant="plain"
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            w="42px"
            h="48px"
            bg="white"
            border="2px solid"
            borderColor="orange.200"
            borderRadius="10px"
            px="4px"
            cursor="default"
            _hover={{ bg: 'orange.50' }}
            transition="background 0.15s"
            gap="2px"
            aria-label={`${project.comments} comments on ${project.name}`}
          >
            <Box color="gray.800">
              <LuMessageSquare size={18} />
            </Box>
            <Text
              fontSize="sm"
              fontWeight="normal"
              color="gray.800"
              lineHeight="20px"
              textAlign="center"
            >
              {project.comments}
            </Text>
          </Button>
        </motion.div>

        <motion.div
          whileTap={{ scale: 1.2, y: -3 }}
          style={{ display: 'contents' }}
        >
          <Button
            data-project-card-action="true"
            type="button"
            variant="plain"
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            w="44px"
            h="52px"
            overflow="hidden"
            bg={isVoted ? 'orange.50' : 'white'}
            border="2px solid"
            borderColor={isVoted ? 'orange.400' : 'orange.200'}
            borderRadius="10px"
            px="4px"
            _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
            transition="background 0.15s, border-color 0.15s"
            gap="2px"
            onClick={() => void toggleVote()}
            aria-label={`Upvote ${project.name}`}
            aria-pressed={isVoted}
          >
            <Box color={isVoted ? 'orange.500' : 'gray.800'}>
              <LuChevronUp size={18} />
            </Box>
            <Box position="relative" h="20px" w="100%" overflow="hidden">
              <AnimatePresence mode="sync" initial={false}>
                <motion.span
                  key={voteCount}
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
                    color: 'inherit',
                  }}
                >
                  {voteCount}
                </motion.span>
              </AnimatePresence>
            </Box>
          </Button>
        </motion.div>
      </HStack>
    </LinkBox>
  );
}
