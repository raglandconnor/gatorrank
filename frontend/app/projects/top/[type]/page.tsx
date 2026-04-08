'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Box, SimpleGrid, Spinner, VStack, Text } from '@chakra-ui/react';
import { Navbar } from '@/components/Navbar';
import { ProjectGridCard } from '@/components/projects/ProjectGridCard';
import type { Project } from '@/data/mock-projects';
import { listProjectsPublic } from '@/lib/api/projects';
import type { ProjectListQuery } from '@/lib/api/types/project';
import { mapProjectListItemsToCardProjects } from '@/lib/projects/projectCardMapper';

type TopProjectsType =
  | 'top-overall'
  | 'trending-this-month'
  | 'trending-last-month';

function toDateOnly(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getMonthRange(offsetMonths = 0): { from: string; to: string } {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth() + offsetMonths, 1);
  const end = new Date(now.getFullYear(), now.getMonth() + offsetMonths + 1, 0);
  return { from: toDateOnly(start), to: toDateOnly(end) };
}

async function listAllProjects(query: ProjectListQuery): Promise<Project[]> {
  const items: Project[] = [];
  let cursor: string | undefined;

  // Guard to avoid runaway pagination in case of malformed cursors.
  for (let i = 0; i < 20; i += 1) {
    const res = await listProjectsPublic({ ...query, limit: 50, cursor });
    items.push(...mapProjectListItemsToCardProjects(res.items));
    if (!res.next_cursor) break;
    cursor = res.next_cursor;
  }

  return items;
}

export default function TopProjectsPage() {
  const params = useParams();
  const type = (params?.type as string | undefined) ?? '';

  const { title, query } = useMemo(() => {
    const t = type as TopProjectsType;
    const currentMonth = getMonthRange(0);
    const lastMonth = getMonthRange(-1);

    switch (t) {
      case 'top-overall':
        return {
          title: 'Top Overall UF Projects',
          query: { sort: 'top' as const },
        };
      case 'trending-this-month':
        return {
          title: 'Trending UF Projects This Month',
          query: {
            sort: 'top' as const,
            published_from: currentMonth.from,
            published_to: currentMonth.to,
          },
        };
      case 'trending-last-month':
        return {
          title: 'Trending UF Projects Last Month',
          query: {
            sort: 'top' as const,
            published_from: lastMonth.from,
            published_to: lastMonth.to,
          },
        };
      default:
        return { title: 'Projects', query: null };
    }
  }, [type]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!query) {
        setLoading(false);
        setProjects([]);
        setError(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const result = await listAllProjects(query);
        if (cancelled) return;
        setProjects(result);
      } catch (err) {
        if (cancelled) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load projects';
        setError(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [query]);

  return (
    <Box minH="100vh" bg="gray.50">
      <Navbar />

      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto" w="100%">
        <VStack align="start" gap="30px" w="100%">
          <Text
            fontSize="xl"
            fontWeight="bold"
            color="orange.600"
            lineHeight="32px"
            textAlign="center"
            w="100%"
          >
            {title}
          </Text>

          {loading ? (
            <VStack
              minH="40vh"
              justify="center"
              align="center"
              w="100%"
              gap="12px"
            >
              <Spinner size="lg" color="orange.400" />
              <Text fontSize="sm" color="gray.600">
                Loading projects...
              </Text>
            </VStack>
          ) : error ? (
            <Box
              bg="white"
              borderRadius="16px"
              border="1px solid"
              borderColor="gray.200"
              p="20px"
              w="100%"
            >
              <Text fontSize="md" color="gray.700">
                Could not load projects.
              </Text>
              <Text fontSize="sm" color="gray.600">
                {error}
              </Text>
            </Box>
          ) : projects.length === 0 ? (
            <Box
              bg="white"
              borderRadius="16px"
              border="1px solid"
              borderColor="gray.200"
              p="20px"
            >
              <Text fontSize="md" color="gray.600">
                No projects found for this section.
              </Text>
            </Box>
          ) : (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap="20px" w="100%">
              {projects.map((project, idx) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.35, delay: idx * 0.07 }}
                  style={{ width: '100%', height: '100%' }}
                >
                  <ProjectGridCard project={project} rank={idx + 1} />
                </motion.div>
              ))}
            </SimpleGrid>
          )}
        </VStack>
      </Box>
    </Box>
  );
}
