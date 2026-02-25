'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import NextLink from 'next/link';
import {
  Box,
  Button,
  Field,
  Flex,
  Heading,
  IconButton,
  Input,
  InputGroup,
  Link,
  Stack,
  Text,
} from '@chakra-ui/react';
import { HiEye, HiEyeSlash } from 'react-icons/hi2';

function GatorRankLogo() {
  return (
    <Box
      position="relative"
      width={{ base: '100px', sm: '120px', md: '140px' }}
      height={{ base: '100px', sm: '120px', md: '140px' }}
      flexShrink={0}
    >
      <Image
        src="/logo.svg"
        alt="GatorRank"
        fill
        sizes="(max-width: 640px) 100px, (max-width: 768px) 120px, 140px"
        style={{ objectFit: 'contain' }}
        priority
      />
    </Box>
  );
}

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <Flex
      minH="100vh"
      bg="#f8f8f8"
      direction="column"
      align="center"
      justify="flex-start"
      pt={{ base: 12, sm: 16 }}
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
          <Link as={NextLink} href="/" display="block">
            <motion.div
              whileHover={{ scale: 1.08 }}
              transition={{ duration: 0.2 }}
              style={{ display: 'inline-block' }}
            >
              <GatorRankLogo />
            </motion.div>
          </Link>
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

        <Box
          bg="white"
          borderRadius="xl"
          p={{ base: 6, sm: 8 }}
          width="100%"
          boxShadow="sm"
        >
          <Stack as="form" gap={5} onSubmit={(e) => e.preventDefault()}>
            <Field.Root>
              <Field.Label fontWeight="500" color="gray.800" mb="2">
                Full Name
              </Field.Label>
              <Input
                type="text"
                placeholder="Your name"
                size="md"
                variant="outline"
                color="gray.900"
                borderColor="gray.200"
                _placeholder={{ color: 'gray.400' }}
              />
            </Field.Root>

            <Field.Root>
              <Field.Label fontWeight="500" color="gray.800" mb="2">
                Email
              </Field.Label>
              <Input
                type="email"
                placeholder="your.name@university.edu"
                size="md"
                variant="outline"
                color="gray.900"
                borderColor="gray.200"
                _placeholder={{ color: 'gray.400' }}
              />
            </Field.Root>

            <Field.Root>
              <Field.Label fontWeight="500" color="gray.800" mb="2">
                Password
              </Field.Label>
              <InputGroup
                endElement={
                  <IconButton
                    type="button"
                    variant="ghost"
                    onClick={() => setShowPassword((p) => !p)}
                    aria-label={
                      showPassword ? 'Hide password' : 'Show password'
                    }
                    color="gray.500"
                    _hover={{ color: 'gray.700' }}
                    size="sm"
                    cursor="pointer"
                  >
                    {showPassword ? (
                      <HiEyeSlash size={20} />
                    ) : (
                      <HiEye size={20} />
                    )}
                  </IconButton>
                }
              >
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  size="md"
                  variant="outline"
                  color="gray.900"
                  borderColor="gray.200"
                  _placeholder={{ color: 'gray.400' }}
                  pe="10"
                />
              </InputGroup>
            </Field.Root>

            <Field.Root>
              <Field.Label fontWeight="500" color="gray.800" mb="2">
                Confirm Password
              </Field.Label>
              <InputGroup
                endElement={
                  <IconButton
                    type="button"
                    variant="ghost"
                    onClick={() => setShowConfirmPassword((p) => !p)}
                    aria-label={
                      showConfirmPassword ? 'Hide password' : 'Show password'
                    }
                    color="gray.500"
                    _hover={{ color: 'gray.700' }}
                    size="sm"
                    cursor="pointer"
                  >
                    {showConfirmPassword ? (
                      <HiEyeSlash size={20} />
                    ) : (
                      <HiEye size={20} />
                    )}
                  </IconButton>
                }
              >
                <Input
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  size="md"
                  variant="outline"
                  color="gray.900"
                  borderColor="gray.200"
                  _placeholder={{ color: 'gray.400' }}
                  pe="10"
                />
              </InputGroup>
            </Field.Root>

            <Button
              type="submit"
              bg="#FF8C38"
              color="white"
              _hover={{ bg: '#E67A2E' }}
              _active={{ bg: '#CC6B28' }}
              size="md"
              fontWeight="600"
              borderRadius="lg"
              py={6}
              mt={4}
            >
              Sign Up
            </Button>
          </Stack>
        </Box>

        <Link
          as={NextLink}
          href="/login"
          color="#FF8C38"
          fontSize={{ base: 'sm', sm: 'md' }}
          fontWeight="500"
          _hover={{ color: '#E67A2E', textDecoration: 'underline' }}
        >
          Already have an account? Sign in
        </Link>
      </Stack>
    </Flex>
  );
}
