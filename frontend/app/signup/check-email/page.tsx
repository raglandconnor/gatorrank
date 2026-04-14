import NextLink from 'next/link';
import {
  Box,
  Button,
  Flex,
  Heading,
  Link,
  Stack,
  Text,
} from '@chakra-ui/react';

import { GatorRankLogo } from '@/components/layout/GatorRankLogo';

type CheckEmailPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CheckEmailPage({
  searchParams,
}: CheckEmailPageProps) {
  const params = (await searchParams) ?? {};
  const email = typeof params.email === 'string' ? params.email : null;

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
        maxW="440px"
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
              Check Your Email
            </Heading>
            <Text fontSize={{ base: 'sm', sm: 'md' }} color="gray.600">
              We sent a confirmation link to {email ?? 'your inbox'}.
            </Text>
            <Text fontSize={{ base: 'sm', sm: 'md' }} color="gray.600">
              Open that link to activate your account, then sign in.
            </Text>
          </Stack>
        </Stack>

        <Box
          bg="white"
          borderRadius="xl"
          p={{ base: 6, sm: 8 }}
          width="100%"
          boxShadow="sm"
        >
          <Stack gap={3}>
            <Button
              asChild
              bg="#FF8C38"
              color="white"
              _hover={{ bg: '#E67A2E' }}
              _active={{ bg: '#CC6B28' }}
              size="md"
              fontWeight="600"
              borderRadius="lg"
              py={6}
            >
              <NextLink href="/login">Go to Login</NextLink>
            </Button>
            <Link
              asChild
              color="#FF8C38"
              fontSize={{ base: 'sm', sm: 'md' }}
              fontWeight="500"
              _hover={{ color: '#E67A2E', textDecoration: 'underline' }}
            >
              <NextLink href="/signup">
                Didn&apos;t get the email? Try signing up again
              </NextLink>
            </Link>
          </Stack>
        </Box>
      </Stack>
    </Flex>
  );
}
