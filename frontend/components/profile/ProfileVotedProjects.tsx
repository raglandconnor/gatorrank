'use client';

import { useEffect, useState } from 'react';
import { SimpleGrid, Text, VStack } from '@chakra-ui/react';
import { getMyVotedProjects } from '@/lib/api/users';
import type { ProjectListItem } from '@/lib/api/types/project';
import { ProjectCollectionLoading } from '@/components/projects/ProjectCollectionLoading';
import { UserProjectCard } from '@/components/profile/ProfileUserProjects';

export function ProfileVotedProjects() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getMyVotedProjects({ limit: 20 });
        setProjects(data.items);
      } catch {
        setError('Could not load voted projects.');
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  if (loading) return <ProjectCollectionLoading variant="grid" count={3} />;

  if (error) {
    return (
      <Text fontSize="sm" color="red.500">
        {error}
      </Text>
    );
  }

  if (projects.length === 0) {
    return (
      <VStack align="start" gap="14px" w="100%">
        <Text fontSize="sm" color="gray.500" lineHeight="24px">
          You haven&apos;t voted for any projects yet. Explore projects and
          upvote the ones you find interesting!
        </Text>
        <ProjectCollectionLoading
          variant="grid"
          count={3}
          showMessage={false}
        />
      </VStack>
    );
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap="16px" w="100%">
      {projects.map((project) => (
        <UserProjectCard key={project.id} project={project} />
      ))}
    </SimpleGrid>
  );
}
