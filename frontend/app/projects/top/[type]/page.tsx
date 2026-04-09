'use client';

import { useMemo } from 'react';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Box, SimpleGrid, VStack, Text } from '@chakra-ui/react';
import { Navbar } from '@/components/layout/Navbar';
import { ProjectGridCard } from '@/components/projects/ProjectGridCard';
import {
  topOverallProjects,
  trendingThisMonthProjects,
  trendingLastMonthProjects,
} from '@/data/mock-projects';

type TopProjectsType =
  | 'top-overall'
  | 'trending-this-month'
  | 'trending-last-month';

export default function TopProjectsPage() {
  const params = useParams();
  const type = (params?.type as string | undefined) ?? '';

  const { title, projects } = useMemo(() => {
    const t = type as TopProjectsType;
    switch (t) {
      case 'top-overall':
        return {
          title: 'Top Overall UF Projects',
          projects: topOverallProjects,
        };
      case 'trending-this-month':
        return {
          title: 'Trending UF Projects This Month',
          projects: trendingThisMonthProjects,
        };
      case 'trending-last-month':
        return {
          title: 'Trending UF Projects Last Month',
          projects: trendingLastMonthProjects,
        };
      default:
        return { title: 'Projects', projects: [] };
    }
  }, [type]);

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

          {projects.length === 0 ? (
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
