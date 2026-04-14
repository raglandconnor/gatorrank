'use client';

import { Badge, HStack, Wrap } from '@chakra-ui/react';
import { LuLayoutGrid, LuHash, LuCodeXml } from 'react-icons/lu';

interface ProjectTaxonomyBadgesProps {
  categories: string[];
  tags: string[];
  techStack: string[];
}

export function ProjectTaxonomyBadges({
  categories,
  tags,
  techStack,
}: ProjectTaxonomyBadgesProps) {
  const hasAny =
    categories.length > 0 || tags.length > 0 || techStack.length > 0;

  if (!hasAny) return null;

  return (
    <Wrap gap="6px" w="100%">
      {categories.map((name) => (
        <Badge
          key={name}
          bg="orange.100"
          color="orange.800"
          borderRadius="full"
          px="10px"
          py="3px"
          fontSize="xs"
          fontWeight="semibold"
          textTransform="none"
          letterSpacing="0.01em"
        >
          <HStack gap="4px" display="inline-flex" align="center">
            <LuLayoutGrid size={10} />
            {name}
          </HStack>
        </Badge>
      ))}
      {tags.map((name) => (
        <Badge
          key={name}
          bg="white"
          border="1px solid"
          borderColor="orange.200"
          color="gray.700"
          borderRadius="8px"
          px="10px"
          py="3px"
          fontSize="xs"
          fontWeight="medium"
          textTransform="none"
          letterSpacing="0.01em"
        >
          <HStack gap="4px" display="inline-flex" align="center">
            <LuHash size={10} />
            {name}
          </HStack>
        </Badge>
      ))}
      {techStack.map((name) => (
        <Badge
          key={name}
          bg="blue.50"
          color="blue.700"
          border="1px solid"
          borderColor="blue.200"
          borderRadius="6px"
          px="8px"
          py="3px"
          fontSize="xs"
          fontWeight="medium"
          textTransform="none"
          fontFamily="mono"
        >
          <HStack gap="4px" display="inline-flex" align="center">
            <LuCodeXml size={10} />
            {name}
          </HStack>
        </Badge>
      ))}
    </Wrap>
  );
}
