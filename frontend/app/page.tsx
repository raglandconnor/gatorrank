'use client';
import { Box, Container, VStack } from '@chakra-ui/react';
import { Navbar } from '@/components/Navbar';
import { ProjectSection } from '@/components/ProjectSection';
import {
  topOverallProjects,
  trendingThisMonthProjects,
  trendingLastMonthProjects,
} from '@/data/mock-projects';

export default function Home() {
  return (
    <Box minH="100vh" bg="gray.50">
      <Navbar />
      <Container maxW="1280px" px="212px" py="50px">
        <VStack gap="96px" align="start">
          <ProjectSection
            title="Top Overall UF Projects"
            projects={topOverallProjects}
            ctaLabel="See all top UF projects"
          />
          <ProjectSection
            title="Trending UF Projects This Month"
            projects={trendingThisMonthProjects}
            ctaLabel="See all trending UF projects this month"
          />
          <ProjectSection
            title="Trending UF Projects Last Month"
            projects={trendingLastMonthProjects}
            ctaLabel="See all trending UF projects last month"
          />
        </VStack>
      </Container>
    </Box>
  );
}
