'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Box, SimpleGrid, VStack, Text } from '@chakra-ui/react';
import { Navbar } from '@/components/layout/Navbar';
import { ProjectGridCard } from '@/components/projects/ProjectGridCard';
import { ProjectCollectionLoading } from '@/components/projects/ProjectCollectionLoading';
import type { Project } from '@/types/project';
import { listProjectsPublic } from '@/lib/api/projects';
import type { ProjectListQuery } from '@/lib/api/types/project';
import { getAllTimeTopRange, getMonthRange } from '@/lib/projects/dateFilters';
import { mapProjectListItemsToCardProjects } from '@/lib/projects/projectCardMapper';

type TopProjectsType =
  | 'top-overall'
  | 'trending-this-month'
  | 'trending-last-month';

const TOP_PROJECTS_PAGE_SIZE = 50;
const TOP_PROJECTS_MAX_PAGES = 20;

async function listAllProjects(query: ProjectListQuery): Promise<Project[]> {
  const items: Project[] = [];
  let cursor: string | undefined;
  let hasMore = false;

  // Guard to avoid runaway pagination in case of malformed cursors.
  for (let i = 0; i < TOP_PROJECTS_MAX_PAGES; i += 1) {
    const res = await listProjectsPublic({
      ...query,
      limit: TOP_PROJECTS_PAGE_SIZE,
      cursor,
    });
    items.push(...mapProjectListItemsToCardProjects(res.items));
    if (!res.next_cursor) {
      hasMore = false;
      break;
    }
    hasMore = true;
    cursor = res.next_cursor;
  }

  if (hasMore) {
    throw new Error(
      `Too many projects to load at once (>${TOP_PROJECTS_MAX_PAGES * TOP_PROJECTS_PAGE_SIZE}). Please narrow the filter or use pagination.`,
    );
  }

  return items;
}

export default function TopProjectsPage() {
  const params = useParams();
  const type = (params?.type as string | undefined) ?? '';

  const { title, query } = useMemo(() => {
    const t = type as TopProjectsType;
    const topOverall = getAllTimeTopRange();
    const currentMonth = getMonthRange(0);
    const lastMonth = getMonthRange(-1);

    switch (t) {
      case 'top-overall':
        return {
          title: 'Top Overall UF Projects',
          query: {
            sort: 'top' as const,
            published_from: topOverall.from,
            published_to: topOverall.to,
          },
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

      <Box
        px={{ base: '16px', md: '24px', lg: '36px' }}
        pt="32px"
        pb="64px"
        maxW="1280px"
        mx="auto"
        w="100%"
      >
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
            <ProjectCollectionLoading variant="grid" count={6} />
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
                  viewport={{ once: true, margin: '0px 0px -12% 0px' }}
                  transition={{ duration: 0.26, delay: (idx % 6) * 0.03 }}
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
