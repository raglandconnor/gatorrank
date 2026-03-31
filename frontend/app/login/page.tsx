'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { GatorRankLogo } from '@/components/GatorRankLogo';
import { useAuth } from '@/components/auth/AuthProvider';
import { toast } from '@/lib/ui/toast';
import { loginErrorToast } from '@/lib/auth/toastMessages';
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
import NextLink from 'next/link';
import { isValidEduEmail } from '@/lib/validation';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isReady } = useAuth();

  useEffect(() => {
    if (searchParams.get('signedOut') === '1') {
      toast.success({
        title: 'Signed out',
        description: 'You have been successfully signed out.',
      });
      router.replace('/login');
    }
  }, [searchParams, router]);

  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
  }>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const newErrors: typeof errors = {};

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!isValidEduEmail(email)) {
      newErrors.email = 'Please enter a valid .edu email address';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await login(email.trim(), password, rememberMe);
      toast.success({
        title: 'Signed in',
        description: 'Welcome back. Taking you to your profile…',
      });
      router.push('/profile');
    } catch (err) {
      toast.error(loginErrorToast(err));
    } finally {
      setIsSubmitting(false);
    }
  }

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
              Welcome Back
            </Heading>
            <Text fontSize={{ base: 'sm', sm: 'md' }} color="gray.600">
              Sign in to access your projects
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
          <Stack as="form" gap={5} onSubmit={handleSubmit}>
            <Field.Root invalid={!!errors.email}>
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
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email)
                    setErrors((prev) => ({ ...prev, email: undefined }));
                }}
              />
              {errors.email && (
                <Field.ErrorText
                  color="red.500"
                  mt="1"
                  fontSize="xs"
                  textAlign="left"
                >
                  {errors.email}
                </Field.ErrorText>
              )}
            </Field.Root>

            <Field.Root invalid={!!errors.password}>
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
                  placeholder="Enter your password"
                  size="md"
                  variant="outline"
                  color="gray.900"
                  borderColor="gray.200"
                  _placeholder={{ color: 'gray.400' }}
                  pe="10"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password)
                      setErrors((prev) => ({ ...prev, password: undefined }));
                  }}
                />
              </InputGroup>
              {errors.password && (
                <Field.ErrorText
                  color="red.500"
                  mt="1"
                  fontSize="xs"
                  textAlign="left"
                >
                  {errors.password}
                </Field.ErrorText>
              )}
            </Field.Root>

            <Box
              as="label"
              display="flex"
              alignItems="center"
              gap={2}
              justifyContent="flex-start"
              cursor="pointer"
            >
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              <Text fontSize="sm" color="gray.700" textAlign="left">
                Remember me
              </Text>
            </Box>

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
              disabled={!isReady || isSubmitting}
            >
              {isSubmitting ? 'Signing in…' : 'Sign In'}
            </Button>
          </Stack>
        </Box>

        <Stack gap={1} align="center">
          <Link
            as={NextLink}
            href="/signup"
            color="#FF8C38"
            fontSize={{ base: 'sm', sm: 'md' }}
            fontWeight="500"
            _hover={{ color: '#E67A2E', textDecoration: 'underline' }}
          >
            Don&apos;t have an account? Sign up
          </Link>
          <Link
            href="#"
            color="#FF8C38"
            fontSize={{ base: 'sm', sm: 'md' }}
            fontWeight="500"
            _hover={{ color: '#E67A2E', textDecoration: 'underline' }}
          >
            Forgot password?
          </Link>
        </Stack>
      </Stack>
    </Flex>
  );
}
