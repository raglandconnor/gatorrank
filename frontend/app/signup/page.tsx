'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { GatorRankLogo } from '@/components/GatorRankLogo';
import { useAuth } from '@/components/auth/AuthProvider';
import { toaster } from '@/components/ui/toaster';
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
import {
  isValidEduEmail,
  isValidName,
  isValidPassword,
} from '@/lib/validation';

export default function SignupPage() {
  const router = useRouter();
  const { signup, isReady } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const newErrors: typeof errors = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (!isValidName(fullName)) {
      newErrors.fullName =
        'Name can only contain letters, spaces, hyphens, and apostrophes';
    }

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!isValidEduEmail(email)) {
      newErrors.email = 'Please enter a valid .edu email address';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (!isValidPassword(password)) {
      newErrors.password =
        'Password must be 12–128 characters (not only spaces), matching server rules';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      await signup({
        email: email.trim(),
        password,
        fullName: fullName.trim(),
        rememberMe,
      });
      toaster.success({
        title: 'Account created',
        description: 'You are signed in.',
      });
      router.push('/profile');
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Could not create account.';
      toaster.error({
        title: 'Sign up failed',
        description: message,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Flex
      minH="100vh"
      bg="#f8f8f8"
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

        <Box
          bg="white"
          borderRadius="xl"
          p={{ base: 6, sm: 8 }}
          width="100%"
          boxShadow="sm"
        >
          <Stack as="form" gap={5} onSubmit={handleSubmit}>
            <Field.Root invalid={!!errors.fullName}>
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
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  if (errors.fullName)
                    setErrors((prev) => ({ ...prev, fullName: undefined }));
                }}
              />
              {errors.fullName && (
                <Field.ErrorText
                  color="red.500"
                  mt="1"
                  fontSize="xs"
                  textAlign="left"
                >
                  {errors.fullName}
                </Field.ErrorText>
              )}
            </Field.Root>

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
                  placeholder="Create a password"
                  size="md"
                  variant="outline"
                  color="gray.900"
                  borderColor="gray.200"
                  _placeholder={{ color: 'gray.400' }}
                  pe="10"
                  value={password}
                  onChange={(e) => {
                    const value = e.target.value;
                    setPassword(value);
                    if (errors.password)
                      setErrors((prev) => ({ ...prev, password: undefined }));
                    if (confirmPassword) {
                      setErrors((prev) => ({
                        ...prev,
                        confirmPassword:
                          value !== confirmPassword
                            ? 'Passwords do not match'
                            : undefined,
                      }));
                    }
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

            <Field.Root invalid={!!errors.confirmPassword}>
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
                      showConfirmPassword
                        ? 'Hide confirm password'
                        : 'Show confirm password'
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
                  value={confirmPassword}
                  onChange={(e) => {
                    const value = e.target.value;
                    setConfirmPassword(value);
                    setErrors((prev) => ({
                      ...prev,
                      confirmPassword:
                        value && value !== password
                          ? 'Passwords do not match'
                          : undefined,
                    }));
                  }}
                />
              </InputGroup>
              {errors.confirmPassword && (
                <Field.ErrorText
                  color="red.500"
                  mt="1"
                  fontSize="xs"
                  textAlign="left"
                >
                  {errors.confirmPassword}
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
              mt={4}
              disabled={!isReady || isSubmitting}
            >
              {isSubmitting ? 'Creating account…' : 'Sign Up'}
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
