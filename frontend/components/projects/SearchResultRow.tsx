'use client';

import NextLink from 'next/link';
import {
  Box,
  HStack,
  Text,
  VStack,
  Link as ChakraLink,
  Badge,
} from '@chakra-ui/react';
import { LuArrowRight, LuChevronUp, LuUsers } from 'react-icons/lu';
import type { SearchProjectListItem } from '@/lib/api/types/search';

interface SearchResultRowProps {
  project: SearchProjectListItem;
}

function formatPublishedDate(value: string | null): string {
  if (!value) return 'Unpublished';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return 'Unknown date';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed);
}

export function SearchResultRow({ project }: SearchResultRowProps) {
  const taxonomy = project.tags.length > 0 ? project.tags : project.categories;

  return (
    <ChakraLink
      as={NextLink}
      href={`/projects/${project.id}`}
      _hover={{ textDecoration: 'none' }}
      w="100%"
    >
      <HStack
        bg="gray.100"
        borderRadius="13px"
        px={{ base: '14px', md: '20px' }}
        py={{ base: '12px', md: '14px' }}
        gap={{ base: '12px', md: '20px' }}
        align="stretch"
        w="100%"
        transition="background 0.15s"
        _hover={{ bg: '#efefef' }}
      >
        <VStack align="start" gap="8px" flex="1" minW={0}>
          <HStack gap="8px" align="center" w="100%">
            <Text
              fontSize="md"
              fontWeight="bold"
              color="gray.900"
              lineHeight="24px"
              lineClamp={1}
            >
              {project.title}
            </Text>
            <Box color="orange.600" flexShrink={0}>
              <LuArrowRight size={13} />
            </Box>
          </HStack>

          <Text fontSize="sm" color="gray.700" lineHeight="22px" lineClamp={2}>
            {project.short_description}
          </Text>

          <HStack gap="8px" flexWrap="wrap">
            {taxonomy.slice(0, 4).map((term) => (
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
        </VStack>

        <VStack align="end" justify="space-between" minW="124px" flexShrink={0}>
          <HStack gap="8px" color="gray.700">
            <LuChevronUp size={14} />
            <Text fontSize="sm" fontWeight="semibold" lineHeight="20px">
              {project.vote_count}
            </Text>
          </HStack>

          <HStack gap="8px" color="gray.600">
            <LuUsers size={14} />
            <Text fontSize="xs" lineHeight="18px">
              Team {project.team_size}
            </Text>
          </HStack>

          <Text fontSize="xs" color="gray.500" lineHeight="18px">
            {formatPublishedDate(project.published_at)}
          </Text>
        </VStack>
      </HStack>
    </ChakraLink>
  );
}
