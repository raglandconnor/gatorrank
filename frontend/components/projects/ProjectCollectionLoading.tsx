'use client';

import {
  Box,
  Flex,
  HStack,
  SimpleGrid,
  Spinner,
  VStack,
  Text,
} from '@chakra-ui/react';

function ProjectRowSkeleton() {
  return (
    <Box bg="gray.100" borderRadius="13px" px="20px" py="9px" w="100%">
      <HStack gap="20px" align="flex-start" w="100%">
        <Box
          w="60px"
          h="60px"
          bg="gray.300"
          borderRadius="13px"
          flexShrink={0}
        />
        <VStack align="start" gap="8px" flex="1" minW={0} pt="2px">
          <Box h="18px" w="48%" bg="gray.300" borderRadius="full" />
          <Box h="16px" w="62%" bg="gray.200" borderRadius="full" />
          <Box h="14px" w="38%" bg="gray.200" borderRadius="full" />
        </VStack>
        <HStack gap="14px" flexShrink={0} pt="6px">
          <Box
            h="48px"
            w="42px"
            bg="white"
            borderRadius="10px"
            border="1px solid"
            borderColor="orange.100"
          />
          <Box
            h="52px"
            w="44px"
            bg="white"
            borderRadius="10px"
            border="1px solid"
            borderColor="orange.100"
          />
        </HStack>
      </HStack>
    </Box>
  );
}

function ProjectGridSkeleton({ titleWidth }: { titleWidth: string }) {
  return (
    <Box
      bg="gray.100"
      borderRadius="13px"
      p={{ base: '20px', md: '24px' }}
      w="100%"
    >
      <VStack align="stretch" gap="16px" w="100%">
        <HStack align="stretch" gap="14px" w="100%">
          <Box
            w="72px"
            h="72px"
            bg="gray.300"
            borderRadius="10px"
            flexShrink={0}
          />
          <VStack align="start" gap="8px" flex="1" minW={0}>
            <Box h="18px" w={titleWidth} bg="gray.300" borderRadius="full" />
            <Box h="14px" w="78%" bg="gray.200" borderRadius="full" />
            <Box h="14px" w="56%" bg="gray.200" borderRadius="full" />
          </VStack>
        </HStack>
        <Box h="56px" w="100%" bg="gray.200" borderRadius="10px" />
        <HStack gap="8px">
          <Box
            h="42px"
            w="76px"
            bg="white"
            borderRadius="12px"
            border="1px solid"
            borderColor="orange.100"
          />
          <Box
            h="42px"
            w="76px"
            bg="white"
            borderRadius="12px"
            border="1px solid"
            borderColor="orange.100"
          />
        </HStack>
      </VStack>
    </Box>
  );
}

interface ProjectCollectionLoadingProps {
  variant: 'row' | 'grid';
  count?: number;
  showMessage?: boolean;
}

export function ProjectCollectionLoading({
  variant,
  count = 3,
  showMessage = true,
}: ProjectCollectionLoadingProps) {
  return (
    <VStack align="stretch" gap="14px" w="100%">
      {showMessage ? (
        <Flex align="center" gap="10px">
          <Spinner size="sm" color="orange.400" />
          <Text fontSize="sm" color="gray.500">
            Loading projects...
          </Text>
        </Flex>
      ) : null}

      {variant === 'row' ? (
        <VStack align="stretch" gap="20px" w="100%">
          {Array.from({ length: count }, (_, index) => (
            <ProjectRowSkeleton key={index} />
          ))}
        </VStack>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} gap="16px" w="100%">
          {Array.from({ length: count }, (_, index) => (
            <ProjectGridSkeleton
              key={index}
              titleWidth={index % 2 === 0 ? '66%' : '54%'}
            />
          ))}
        </SimpleGrid>
      )}
    </VStack>
  );
}
