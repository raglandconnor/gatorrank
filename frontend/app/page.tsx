'use client';
import { useEffect, useState } from 'react';
import { Box, Container, Text, VStack } from '@chakra-ui/react';
import { Navbar } from '@/components/layout/Navbar';
import { ProjectSection } from '@/components/projects/ProjectSection';
import type { Project } from '@/types/project';
import { listProjectsPublic } from '@/lib/api/projects';
import { getAllTimeTopRange, getMonthRange } from '@/lib/projects/dateFilters';
import { mapProjectListItemsToCardProjects } from '@/lib/projects/projectCardMapper';

type HomeProjectsState = {
  loading: boolean;
  error: string | null;
  topOverall: Project[];
  trendingThisMonth: Project[];
  trendingLastMonth: Project[];
};

export default function Home() {
  const [state, setState] = useState<HomeProjectsState>({
    loading: true,
    error: null,
    topOverall: [],
    trendingThisMonth: [],
    trendingLastMonth: [],
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const topOverall = getAllTimeTopRange();
        const currentMonth = getMonthRange(0);
        const lastMonth = getMonthRange(-1);

        const [overallRes, thisMonthRes, lastMonthRes] = await Promise.all([
          listProjectsPublic({
            sort: 'top',
            limit: 5,
            published_from: topOverall.from,
            published_to: topOverall.to,
          }),
          listProjectsPublic({
            sort: 'top',
            limit: 5,
            published_from: currentMonth.from,
            published_to: currentMonth.to,
          }),
          listProjectsPublic({
            sort: 'top',
            limit: 5,
            published_from: lastMonth.from,
            published_to: lastMonth.to,
          }),
        ]);

        if (cancelled) return;
        setState({
          loading: false,
          error: null,
          topOverall: mapProjectListItemsToCardProjects(overallRes.items),
          trendingThisMonth: mapProjectListItemsToCardProjects(
            thisMonthRes.items,
          ),
          trendingLastMonth: mapProjectListItemsToCardProjects(
            lastMonthRes.items,
          ),
        });
      } catch (error) {
        if (cancelled) return;
        const message =
          error instanceof Error ? error.message : 'Failed to load projects';
        setState((prev) => ({ ...prev, loading: false, error: message }));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />
      <Container maxW="1280px" px="212px" py="50px">
        {state.error ? (
          <VStack
            minH="40vh"
            justify="center"
            align="center"
            w="100%"
            gap="8px"
          >
            <Text fontSize="md" color="gray.700">
              Could not load home projects.
            </Text>
            <Text fontSize="sm" color="gray.600">
              {state.error}
            </Text>
          </VStack>
        ) : (
          <VStack gap="96px" align="start">
            <ProjectSection
              title="Top Overall UF Projects"
              projects={state.topOverall}
              loading={state.loading}
              ctaLabel="See all top UF projects"
              ctaHref="/projects/top/top-overall"
            />
            <ProjectSection
              title="Trending UF Projects This Month"
              projects={state.trendingThisMonth}
              loading={state.loading}
              ctaLabel="See all trending UF projects this month"
              ctaHref="/projects/top/trending-this-month"
            />
            <ProjectSection
              title="Trending UF Projects Last Month"
              projects={state.trendingLastMonth}
              loading={state.loading}
              ctaLabel="See all trending UF projects last month"
              ctaHref="/projects/top/trending-last-month"
            />
          </VStack>
        )}
      </Container>
    </Box>
  );
}
