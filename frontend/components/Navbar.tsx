'use client';

import { Box, HStack, Text, Button, Flex } from '@chakra-ui/react';
import Image from 'next/image';
import { LuChevronDown } from 'react-icons/lu';

export function Navbar() {
  return (
    <Box
      as="nav"
      w="100%"
      h="95px"
      borderBottom="0.8px solid"
      borderColor="black"
      px={40}
    >
      <Flex h="100%" align="center" justify="space-between">
        {/* Left side: logo + nav links */}
        <HStack gap="32px" align="center">
          <Box position="relative" w="60px" h="60px" flexShrink={0}>
            <Image
              src="/logo.svg"
              alt="GatorRank"
              fill
              style={{ objectFit: 'contain' }}
              priority
            />
          </Box>

          {/* Categories — stateless hover element */}
          <HStack
            gap="4px"
            cursor="default"
            _hover={{ opacity: 0.7 }}
            transition="opacity 0.15s"
          >
            <Text
              fontSize="md"
              fontWeight="medium"
              color="gray.900"
              lineHeight="30px"
            >
              Categories
            </Text>
            <Box color="gray.900">
              <LuChevronDown size={18} />
            </Box>
          </HStack>

          {/* Groups link */}
          <Text
            fontSize="md"
            fontWeight="medium"
            color="gray.900"
            lineHeight="30px"
            cursor="pointer"
            _hover={{ opacity: 0.7 }}
            transition="opacity 0.15s"
          >
            Groups
          </Text>
        </HStack>

        {/* Right side: Sign Up + Log In */}
        <HStack gap="16px" align="center">
          <Text
            fontSize="md"
            color="gray.900"
            lineHeight="30px"
            cursor="pointer"
            _hover={{ opacity: 0.7 }}
            transition="opacity 0.15s"
          >
            Sign Up
          </Text>
          <Button
            bg="orange.400"
            color="white"
            borderRadius="16px"
            px="20px"
            h="44px"
            fontSize="md"
            fontWeight="normal"
            _hover={{ bg: 'orange.500' }}
            transition="background 0.15s"
          >
            Log In
          </Button>
        </HStack>
      </Flex>
    </Box>
  );
}
