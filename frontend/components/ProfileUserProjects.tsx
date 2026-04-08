'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Badge,
  Box,
  Button,
  Flex,
  HStack,
  SimpleGrid,
  Spinner,
  Text,
  VStack,
} from '@chakra-ui/react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LuMessageSquare,
  LuChevronUp,
  LuArrowRight,
  LuPencil,
} from 'react-icons/lu';
import { getMyProjects, getUserProjectsByUsername } from '@/lib/api/users';
import type { ProjectListItem } from '@/lib/api/types/project';
import { projectEditPath, projectPath } from '@/lib/routes';

function UserProjectCard({
  project,
  onEdit,
}: {
  project: ProjectListItem;
  onEdit?: (slug: string) => void;
}) {
  const router = useRouter();
  const [isHovered, setIsHovered] = useState(false);
  const [isVoted, setIsVoted] = useState(false);
  const voteCount = project.vote_count + (isVoted ? 1 : 0);
  const terms = (
    project.tags.length > 0 ? project.tags : project.categories
  ).slice(0, 2);

  return (
    <Box
      position="relative"
      bg={isHovered ? '#efefef' : 'gray.100'}
      borderRadius="13px"
      p="16px"
      w="100%"
      cursor="pointer"
      transition="background 0.15s"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => router.push(projectPath(project.slug))}
    >
      {onEdit && (
        <Button
          type="button"
          aria-label={`Edit ${project.title}`}
          position="absolute"
          top="12px"
          right="12px"
          zIndex={1}
          size="xs"
          variant="ghost"
          minW="auto"
          h="auto"
          p="6px"
          borderRadius="full"
          bg="white"
          border="1px solid"
          borderColor="gray.300"
          color="gray.600"
          _hover={{ bg: 'gray.100', color: 'gray.800' }}
          transition="background 0.15s, color 0.15s"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(project.slug);
          }}
        >
          <LuPencil size={14} />
        </Button>
      )}

      <VStack align="start" gap="12px">
        <Box
          w="100%"
          h="144px"
          bg="gray.300"
          borderRadius="10px"
          overflow="hidden"
          flexShrink={0}
        />

        <VStack align="start" gap="10px" w="100%">
          <HStack gap="6px" align="center">
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
            <Box
              color="orange.600"
              opacity={isHovered ? 1 : 0}
              transition="opacity 0.15s"
              flexShrink={0}
            >
              <LuArrowRight size={13} />
            </Box>
          </HStack>

          <HStack gap="8px" flexWrap="wrap" minH="28px">
            {terms.map((term) => (
              <Badge
                key={term.id}
                bg="white"
                border="1px solid"
                borderColor="orange.200"
                color="gray.700"
                borderRadius="8px"
                px="8px"
                py="3px"
                fontSize="xs"
                fontWeight="medium"
              >
                {term.name}
              </Badge>
            ))}
          </HStack>

          <HStack gap="8px" mt="2px">
            <motion.div
              whileTap={{ scale: 1.1 }}
              style={{ display: 'contents' }}
            >
              <Flex
                align="center"
                justify="center"
                gap="6px"
                bg="white"
                border="1.6px solid"
                borderColor="orange.200"
                borderRadius="10px"
                px="12px"
                h="36px"
                minW="60px"
                cursor="pointer"
                _hover={{ bg: 'orange.50' }}
                transition="background 0.15s"
                onClick={(e) => e.stopPropagation()}
              >
                <Box color="gray.700">
                  <LuMessageSquare size={14} />
                </Box>
                <Text fontSize="sm" color="gray.700" lineHeight="20px">
                  0
                </Text>
              </Flex>
            </motion.div>

            <motion.div
              whileTap={{ scale: 1.2, y: -3 }}
              style={{ display: 'contents' }}
            >
              <Flex
                align="center"
                justify="center"
                gap="6px"
                bg={isVoted ? 'orange.50' : 'white'}
                border="1.6px solid"
                borderColor={isVoted ? 'orange.400' : 'orange.200'}
                borderRadius="10px"
                px="12px"
                h="36px"
                minW="60px"
                cursor="pointer"
                _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
                transition="background 0.15s, border-color 0.15s"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsVoted((v) => !v);
                }}
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
  const router = useRouter();
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

      {loading && (
        <VStack align="stretch" gap="14px" w="100%">
          <Flex align="center" gap="10px">
            <Spinner size="sm" color="orange.400" />
            <Text fontSize="sm" color="gray.500">
              Loading projects...
            </Text>
          </Flex>
          <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap="16px" w="100%">
            {[0, 1, 2].map((index) => (
              <Box
                key={index}
                bg="gray.100"
                borderRadius="13px"
                p="16px"
                w="100%"
                opacity={0.8}
              >
                <VStack align="start" gap="12px" w="100%">
                  <Box w="100%" h="144px" bg="gray.200" borderRadius="10px" />
                  <VStack align="start" gap="10px" w="100%">
                    <Box
                      h="18px"
                      w={index === 1 ? '70%' : '58%'}
                      bg="gray.300"
                      borderRadius="full"
                    />
                    <HStack gap="8px">
                      <Box
                        h="24px"
                        w="70px"
                        bg="white"
                        borderRadius="8px"
                        border="1px solid"
                        borderColor="orange.100"
                      />
                      <Box
                        h="24px"
                        w="82px"
                        bg="white"
                        borderRadius="8px"
                        border="1px solid"
                        borderColor="orange.100"
                      />
                    </HStack>
                    <HStack gap="8px" mt="2px">
                      <Box
                        h="36px"
                        w="60px"
                        bg="white"
                        borderRadius="10px"
                        border="1px solid"
                        borderColor="orange.100"
                      />
                      <Box
                        h="36px"
                        w="60px"
                        bg="white"
                        borderRadius="10px"
                        border="1px solid"
                        borderColor="orange.100"
                      />
                    </HStack>
                  </VStack>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>
        </VStack>
      )}

      {!loading && error && (
        <Text fontSize="sm" color="red.500">
          {error}
        </Text>
      )}

      {!loading && !error && projects.length === 0 && (
        <Text fontSize="sm" color="gray.400" lineHeight="24px">
          {isOwn
            ? 'No projects yet - add your first one to get noticed on GatorRank.'
            : 'No projects shared yet.'}
        </Text>
      )}

      {!loading && !error && projects.length > 0 && (
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap="16px" w="100%">
          {projects.map((project) => (
            <UserProjectCard
              key={project.id}
              project={project}
              onEdit={
                isOwn ? (slug) => router.push(projectEditPath(slug)) : undefined
              }
            />
          ))}
        </SimpleGrid>
      )}
    </VStack>
  );
}
