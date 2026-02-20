'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, HStack, VStack, Text, Flex } from '@chakra-ui/react';
import {
  LuMessageSquare,
  LuChevronUp,
  LuTag,
  LuArrowRight,
} from 'react-icons/lu';
import type { Project } from '@/data/mock-projects';

interface ProjectCardProps {
  project: Project;
  rank: number;
}

export function ProjectCard({ project, rank }: ProjectCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isVoted, setIsVoted] = useState(false);
  const voteCount = project.votes + (isVoted ? 1 : 0);

  return (
    <HStack
      bg={isHovered ? '#efefef' : 'gray.100'}
      borderRadius="13px"
      px="20px"
      py="9px"
      gap="20px"
      align="center"
      w="100%"
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Icon placeholder */}
      <Box w="42px" h="40px" bg="gray.300" borderRadius="13px" flexShrink={0} />

      {/* Name, description, tags */}
      <VStack align="start" gap="6px" flex={1} justify="center">
        {/* Hoverable title with nav icon */}
        <HStack gap="6px" align="center" display="inline-flex">
          <Text
            fontSize="md"
            fontWeight="bold"
            color={isHovered ? 'orange.600' : 'gray.900'}
            lineHeight="30px"
            transition="color 0.15s"
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

        <Text fontSize="sm" color="gray.800" lineHeight="24px">
          {project.description}
        </Text>

        {/* Tags with hover underline */}
        <HStack gap={0} align="center" flexWrap="wrap">
          <Box color="gray.800" mr="8px">
            <LuTag size={13} />
          </Box>
          {project.tags.map((tag, i) => (
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
          ))}
        </HStack>
      </VStack>

      {/* Action buttons — equal height */}
      <HStack gap="20px" py="17px" flexShrink={0}>
        {/* Comments */}
        <motion.div whileTap={{ scale: 1.1 }} style={{ display: 'contents' }}>
          <Flex
            direction="column"
            align="center"
            justify="center"
            w="44px"
            h="52px"
            bg="white"
            border="2px solid"
            borderColor="orange.200"
            borderRadius="10px"
            px="4px"
            cursor="pointer"
            _hover={{ bg: 'orange.50' }}
            transition="background 0.15s"
            gap="2px"
          >
            <Box color="gray.800">
              <LuMessageSquare size={18} />
            </Box>
            <Text
              fontSize="sm"
              color="gray.800"
              lineHeight="20px"
              textAlign="center"
            >
              {project.comments}
            </Text>
          </Flex>
        </motion.div>

        {/* Votes */}
        <motion.div
          whileTap={{ scale: 1.2, y: -3 }}
          style={{ display: 'contents' }}
        >
          <Flex
            direction="column"
            align="center"
            justify="center"
            w="44px"
            h="52px"
            overflow="hidden"
            bg={isVoted ? 'orange.50' : 'white'}
            border="2px solid"
            borderColor={isVoted ? 'orange.400' : 'orange.200'}
            borderRadius="10px"
            px="4px"
            cursor="pointer"
            _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
            transition="background 0.15s, border-color 0.15s"
            gap="2px"
            onClick={() => setIsVoted((v) => !v)}
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
                    lineHeight: '20px',
                    color: 'inherit',
                  }}
                >
                  {voteCount}
                </motion.span>
              </AnimatePresence>
            </Box>
          </Flex>
        </motion.div>
      </HStack>
    </HStack>
  );
}
