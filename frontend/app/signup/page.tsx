'use client';

import { GatorRankLogo } from '@/components/layout/GatorRankLogo';
import { Flex, Heading, Stack, Text } from '@chakra-ui/react';
import { SignupFormPanel } from './_components/SignupFormPanel';

export default function SignupPage() {
  return (
    <Flex
      minH="100vh"
      bg="transparent"
      direction="column"
      align="center"
      justify="flex-start"
      py={{ base: 4, sm: 6 }}
      px={{ base: 4, sm: 6 }}
    >
      <Stack
        gap={{ base: 6, sm: 8 }}
        width="100%"
        maxW="400px"
        align="center"
        textAlign="center"
      >
        <Stack gap={0} align="center">
          <GatorRankLogo />
          <Stack gap={1}>
            <Heading
              size={{ base: 'xl', sm: '2xl' }}
              fontWeight="700"
              color="gray.800"
            >
              Display Your Projects to the World
            </Heading>
            <Text fontSize={{ base: 'sm', sm: 'md' }} color="gray.600">
              Join the community and showcase your work
            </Text>
          </Stack>
        </Stack>

        <SignupFormPanel />
      </Stack>
    </Flex>
  );
}
