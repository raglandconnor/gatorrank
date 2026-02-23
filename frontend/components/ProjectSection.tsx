'use client';
import { motion } from 'framer-motion';
import { VStack, Text, Button } from '@chakra-ui/react';
import { ProjectCard } from '@/components/ProjectCard';
import type { Project } from '@/data/mock-projects';

interface ProjectSectionProps {
  title: string;
  projects: Project[];
  ctaLabel: string;
}

export function ProjectSection({
  title,
  projects,
  ctaLabel,
}: ProjectSectionProps) {
  return (
    <VStack gap="30px" align="center" w="100%">
      {/* Section heading */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4 }}
        style={{ width: '100%' }}
      >
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
      </motion.div>

      {/* Project cards */}
      <VStack gap="20px" align="start" w="100%">
        {projects.map((project, index) => (
          <motion.div
            key={project.id}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.35, delay: index * 0.07 }}
            style={{ width: '100%' }}
          >
            <ProjectCard project={project} rank={index + 1} />
          </motion.div>
        ))}
      </VStack>

      {/* CTA button */}
      <Button
        bg="orange.400"
        color="white"
        borderRadius="25px"
        h="50px"
        w="100%"
        fontSize="lg"
        fontWeight="normal"
        _hover={{ bg: 'orange.500' }}
        transition="background 0.15s"
      >
        {ctaLabel}
      </Button>
    </VStack>
  );
}
