'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, VStack, HStack, Text, Flex } from '@chakra-ui/react';
import { LuMessageSquare, LuChevronUp, LuArrowRight } from 'react-icons/lu';
import type { ProfileProject } from '@/data/mock-profile';

interface ProfileProjectCardProps {
  project: ProfileProject;
}

export function ProfileProjectCard({ project }: ProfileProjectCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isVoted, setIsVoted] = useState(false);
  const voteCount = project.votes + (isVoted ? 1 : 0);

  return (
    <Box
      bg={isHovered ? '#efefef' : 'gray.100'}
      borderRadius="13px"
      p="16px"
      w="100%"
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <VStack align="start" gap="12px">
        {/* Image placeholder */}
        <Box
          w="100%"
          h="144px"
          bg="gray.300"
          borderRadius="10px"
          overflow="hidden"
          flexShrink={0}
        >
          {project.imageUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={project.imageUrl}
              alt={project.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          )}
        </Box>

        {/* Info */}
        <VStack align="start" gap="6px" w="100%">
          {/* Title + arrow icon */}
          <HStack gap="6px" align="center">
            <Text
              fontSize="md"
              fontWeight="bold"
              color={isHovered ? 'orange.600' : 'gray.900'}
              lineHeight="24px"
              transition="color 0.15s"
            >
              {project.name}
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

          {/* Category */}
          <Text fontSize="xs" color="gray.600" lineHeight="20px">
            {project.category}
          </Text>

          {/* Stats row */}
          <HStack gap="8px" mt="2px">
            {/* Comments */}
            <motion.div
              whileTap={{ scale: 1.1 }}
              style={{ display: 'contents' }}
            >
              <Flex
                align="center"
                justify="center"
                gap="4px"
                bg="white"
                border="1.6px solid"
                borderColor="orange.200"
                borderRadius="10px"
                px="10px"
                h="36px"
                cursor="pointer"
                _hover={{ bg: 'orange.50' }}
                transition="background 0.15s"
              >
                <Box color="gray.700">
                  <LuMessageSquare size={14} />
                </Box>
                <Text fontSize="sm" color="gray.700" lineHeight="20px">
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
                align="center"
                justify="center"
                gap="4px"
                bg={isVoted ? 'orange.50' : 'white'}
                border="1.6px solid"
                borderColor={isVoted ? 'orange.400' : 'orange.200'}
                borderRadius="10px"
                px="10px"
                h="36px"
                cursor="pointer"
                _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
                transition="background 0.15s, border-color 0.15s"
                onClick={() => setIsVoted((v) => !v)}
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
              </Flex>
            </motion.div>
          </HStack>
        </VStack>
      </VStack>
    </Box>
  );
}
