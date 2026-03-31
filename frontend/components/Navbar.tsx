'use client';

import { GatorRankLogo } from '@/components/GatorRankLogo';
import { useAuth } from '@/components/auth/AuthProvider';
import { Box, HStack, Text, Flex, Link, Button } from '@chakra-ui/react';
import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { LuChevronDown, LuLogOut } from 'react-icons/lu';

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? '';
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function Navbar() {
  const { user, isReady, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <Box
      as="nav"
      w="100%"
      h="95px"
      borderBottom="0.8px solid"
      borderColor="black"
    >
      <Box maxW="1280px" mx="auto" px="36px" h="100%">
        <Flex h="100%" align="center" justify="space-between">
          {/* Left side: logo + nav links */}
          <HStack gap="32px" align="center">
            <GatorRankLogo size="sm" />

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

          {/* Right side: auth-aware controls */}
          <HStack gap="16px" align="center" minH="44px">
            {!isReady ? (
              /* Placeholder to prevent layout shift during hydration */
              <Box w="120px" />
            ) : user ? (
              /* Authenticated: profile avatar + logout */
              <HStack gap="12px" align="center">
                <Link
                  as={NextLink}
                  href={`/profile/${user.id}`}
                  _hover={{ textDecoration: 'none', opacity: 0.8 }}
                  transition="opacity 0.15s"
                  aria-label={`Go to ${user.full_name ?? user.email}'s profile`}
                >
                  <HStack gap="10px" align="center">
                    {user.profile_picture_url ? (
                      <img
                        src={user.profile_picture_url}
                        alt={user.full_name ?? user.email}
                        style={{
                          width: '38px',
                          height: '38px',
                          borderRadius: '50%',
                          objectFit: 'cover',
                          flexShrink: 0,
                          display: 'block',
                        }}
                      />
                    ) : (
                      <Flex
                        w="38px"
                        h="38px"
                        borderRadius="full"
                        bg="orange.400"
                        color="white"
                        align="center"
                        justify="center"
                        fontSize="sm"
                        fontWeight="bold"
                        flexShrink={0}
                      >
                        {getInitials(user.full_name ?? user.email)}
                      </Flex>
                    )}
                    <Text
                      fontSize="md"
                      fontWeight="medium"
                      color="gray.900"
                      lineHeight="30px"
                      maxW="120px"
                      overflow="hidden"
                      textOverflow="ellipsis"
                      whiteSpace="nowrap"
                    >
                      {user.full_name ?? user.email}
                    </Text>
                  </HStack>
                </Link>

                <Button
                  variant="ghost"
                  size="sm"
                  color="gray.500"
                  _hover={{ color: 'gray.900' }}
                  aria-label="Log out"
                  onClick={handleLogout}
                  px="8px"
                >
                  <LuLogOut size={18} />
                </Button>
              </HStack>
            ) : (
              /* Unauthenticated: Sign Up + Log In */
              <>
                <Link
                  as={NextLink}
                  href="/signup"
                  fontSize="md"
                  color="gray.900"
                  lineHeight="30px"
                  _hover={{ opacity: 0.7 }}
                  transition="opacity 0.15s"
                >
                  Sign Up
                </Link>
                <Link
                  as={NextLink}
                  href="/login"
                  display="inline-flex"
                  alignItems="center"
                  justifyContent="center"
                  bg="orange.400"
                  color="white"
                  borderRadius="16px"
                  px="20px"
                  h="44px"
                  fontSize="md"
                  fontWeight="normal"
                  _hover={{ bg: 'orange.500' }}
                  transition="background 0.15s"
                  cursor="pointer"
                >
                  Log In
                </Link>
              </>
            )}
          </HStack>
        </Flex>
      </Box>
    </Box>
  );
}
