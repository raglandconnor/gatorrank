'use client';

import NextLink from 'next/link';
import { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  LinkBox,
  LinkOverlay,
} from '@chakra-ui/react';
import { LuArrowRight } from 'react-icons/lu';
import type { Project } from '@/types/project';
import { useProjectVote } from '@/hooks/useProjectVote';
import { projectPath } from '@/lib/routes';
import {
  CommentPill,
  VotePill,
} from '@/components/projects/ProjectActionPills';
import { ProjectTaxonomyBadges } from '@/components/projects/ProjectTaxonomyBadges';

interface ProjectGridCardProps {
  project: Project;
  rank: number;
}

export function ProjectGridCard({ project, rank }: ProjectGridCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const { isVoted, voteCount, isPending, toggleVote } = useProjectVote({
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
      p={{ base: '20px', md: '24px' }}
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        setIsPressed(false);
      }}
      w="100%"
      h="100%"
      display="flex"
      flexDirection="column"
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
      <VStack align="stretch" gap="16px" flex="1">
        <HStack align="stretch" gap="14px" w="100%">
          <Box
            flexShrink={0}
            w="72px"
            h="72px"
            bg="gray.300"
            borderRadius="10px"
            overflow="hidden"
          />

          <VStack
            align="start"
            gap="6px"
            flex="1"
            minW={0}
            justify="flex-start"
          >
            <HStack gap="6px" align="center" w="100%" minW={0}>
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
            <ProjectTaxonomyBadges
              categories={project.categories}
              tags={project.tags}
              techStack={project.tech_stack}
            />
          </VStack>
        </HStack>

        <Text
          position="relative"
          zIndex={1}
          fontSize="sm"
          color="gray.800"
          lineHeight="24px"
          lineClamp={3}
          minH="72px"
          flex="1"
        >
          {project.description}
        </Text>

        <HStack
          gap="8px"
          pt="4px"
          w="100%"
          align="center"
          position="relative"
          zIndex={1}
        >
          <CommentPill
            count={project.comments}
            ariaLabel={`${project.comments} comments on ${project.name}`}
          />
          <VotePill
            count={voteCount}
            active={isVoted}
            pending={isPending}
            ariaLabel={`Upvote ${project.name}`}
            onClick={() => {
              void toggleVote();
            }}
          />
        </HStack>
      </VStack>
    </LinkBox>
  );
}
