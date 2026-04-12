'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, VStack, HStack, Text, Button } from '@chakra-ui/react';
import {
  LuMessageSquare,
  LuChevronUp,
  LuArrowRight,
  LuTag,
} from 'react-icons/lu';
import type { Project } from '@/types/project';
import { useProjectVote } from '@/hooks/useProjectVote';

interface ProjectGridCardProps {
  project: Project;
  rank: number;
}

export function ProjectGridCard({ project, rank }: ProjectGridCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const { isVoted, voteCount, toggleVote } = useProjectVote({
    projectId: String(project.id),
    initialVoteCount: project.votes,
    initialViewerHasVoted: project.viewerHasVoted ?? false,
  });

  return (
    <Box
      bg={isHovered ? '#efefef' : 'gray.100'}
      borderRadius="13px"
      p={{ base: '20px', md: '24px' }}
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      w="100%"
      h="100%"
      display="flex"
      flexDirection="column"
    >
      <VStack align="stretch" gap="14px" flex="1">
        {/* Header: square image (side = row height, matches name + tags) + text */}
        <HStack align="stretch" gap="14px" w="100%">
          <Box
            alignSelf="stretch"
            flexShrink={0}
            minH="72px"
            minW="72px"
            h="100%"
            w="auto"
            aspectRatio="1"
            bg="gray.300"
            borderRadius="10px"
            overflow="hidden"
          />

          <VStack
            align="start"
            gap="4px"
            flex="1"
            minW={0}
            justify="flex-start"
          >
            <HStack gap="6px" align="center" w="100%">
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
              <Box
                color="orange.600"
                opacity={isHovered ? 1 : 0}
                transition="opacity 0.15s"
                flexShrink={0}
              >
                <LuArrowRight size={13} />
              </Box>
            </HStack>
            {/* Tags — same hover style as home ProjectCard */}
            <HStack gap={0} align="center" flexWrap="wrap" w="100%">
              <Box color="gray.800" mr="8px" flexShrink={0}>
                <LuTag size={13} />
              </Box>
              {project.tags.length > 0 ? (
                project.tags.map((tag, i) => (
                  <HStack key={tag} gap={0} align="center">
                    <Text
                      fontSize="sm"
                      color="gray.800"
                      lineHeight="24px"
                      cursor="pointer"
                      _hover={{
                        textDecoration: 'underline',
                        textUnderlineOffset: '2px',
                      }}
                    >
                      {tag}
                    </Text>
                    {i < project.tags.length - 1 && (
                      <Box
                        w="4px"
                        h="4px"
                        borderRadius="full"
                        bg="gray.500"
                        mx="9px"
                      />
                    )}
                  </HStack>
                ))
              ) : (
                <Text
                  fontSize="sm"
                  color="gray.800"
                  lineHeight="24px"
                  cursor="pointer"
                  _hover={{
                    textDecoration: 'underline',
                    textUnderlineOffset: '2px',
                  }}
                >
                  Project
                </Text>
              )}
            </HStack>
          </VStack>
        </HStack>

        {/* Body: full-width description */}
        <Text
          fontSize="sm"
          color="gray.800"
          lineHeight="24px"
          lineClamp={3}
          flex="1"
        >
          {project.description}
        </Text>

        {/* Footer: comments + upvote */}
        <HStack gap="8px" pt="4px" w="100%" align="center">
          <Button
            type="button"
            variant="plain"
            display="flex"
            alignItems="center"
            justifyContent="center"
            gap="8px"
            bg="white"
            border="1.6px solid"
            borderColor="orange.200"
            borderRadius="10px"
            h="36px"
            px="12px"
            minW="auto"
            cursor="default"
            _hover={{ bg: 'orange.50' }}
            _focusVisible={{
              borderColor: 'orange.400',
              boxShadow: '0 0 0 3px rgba(251,146,60,0.35)',
            }}
            transition="background 0.15s, border-color 0.15s, box-shadow 0.15s"
            onClick={(e) => e.stopPropagation()}
            aria-label={`${project.comments} comments on ${project.name}`}
          >
            <Box
              as="span"
              color="gray.700"
              display="flex"
              alignItems="center"
              justifyContent="center"
              lineHeight={0}
            >
              <LuMessageSquare size={14} />
            </Box>
            <Text
              as="span"
              fontSize="sm"
              color="gray.700"
              lineHeight="20px"
              fontVariantNumeric="tabular-nums"
            >
              {project.comments}
            </Text>
          </Button>

          <Button
            type="button"
            variant="plain"
            display="flex"
            alignItems="center"
            justifyContent="center"
            gap="6px"
            bg={isVoted ? 'orange.50' : 'white'}
            border="1.6px solid"
            borderColor={isVoted ? 'orange.400' : 'orange.200'}
            borderRadius="10px"
            h="36px"
            px="10px"
            userSelect="none"
            _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
            _focusVisible={{
              borderColor: 'orange.400',
              boxShadow: '0 0 0 3px rgba(251,146,60,0.35)',
            }}
            transition="background 0.15s, border-color 0.15s, box-shadow 0.15s"
            onClick={(e) => {
              e.stopPropagation();
              void toggleVote();
            }}
            aria-label={`Upvote ${project.name}`}
            aria-pressed={isVoted}
          >
            <Box color={isVoted ? 'orange.500' : 'gray.700'}>
              <LuChevronUp size={14} />
            </Box>
            <Box position="relative" h="20px" w="28px" overflow="hidden">
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
                    lineHeight: '20px',
                    color: isVoted ? 'rgb(234,88,12)' : 'rgb(55,65,81)',
                  }}
                >
                  {voteCount}
                </motion.span>
              </AnimatePresence>
            </Box>
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
}
