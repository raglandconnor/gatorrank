'use client';

import { GatorRankLogo } from '@/components/GatorRankLogo';
import { useAuth } from '@/components/auth/AuthProvider';
import { Box, HStack, Text, Flex, Link, Menu, Portal } from '@chakra-ui/react';
import NextLink from 'next/link';
import { useRouter } from 'next/navigation';
import { LuChevronDown, LuUser, LuPlus, LuLogOut } from 'react-icons/lu';

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
    router.push('/login?signedOut=1');
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
          </HStack>

          {/* Right side: auth-aware controls */}
          <HStack gap="16px" align="center" minH="44px">
            {!isReady ? (
              /* Placeholder to prevent layout shift during hydration */
              <Box w="120px" />
            ) : user ? (
              /* Authenticated: avatar dropdown */
              <Menu.Root>
                <Menu.Trigger asChild>
                  <HStack
                    gap="10px"
                    align="center"
                    cursor="pointer"
                    _hover={{ opacity: 0.8 }}
                    transition="opacity 0.15s"
                    tabIndex={0}
                  >
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
                    <Box color="gray.600">
                      <LuChevronDown size={16} />
                    </Box>
                  </HStack>
                </Menu.Trigger>

                <Portal>
                  <Menu.Positioner>
                    <Menu.Content
                      minW="180px"
                      borderRadius="12px"
                      border="1px solid"
                      borderColor="gray.200"
                      boxShadow="md"
                      py="6px"
                      bg="white"
                    >
                      <Menu.Item
                        value="view-profile"
                        onClick={() => router.push(`/profile/${user.id}`)}
                        px="14px"
                        py="10px"
                        fontSize="sm"
                        color="gray.800"
                        _hover={{ bg: 'gray.50' }}
                        cursor="pointer"
                        display="flex"
                        alignItems="center"
                        gap="10px"
                      >
                        <Box color="gray.600">
                          <LuUser size={15} />
                        </Box>
                        View Profile
                      </Menu.Item>

                      <Menu.Item
                        value="add-project"
                        onClick={() => router.push('/projects/create')}
                        px="14px"
                        py="10px"
                        fontSize="sm"
                        color="gray.800"
                        _hover={{ bg: 'gray.50' }}
                        cursor="pointer"
                        display="flex"
                        alignItems="center"
                        gap="10px"
                      >
                        <Box color="gray.600">
                          <LuPlus size={15} />
                        </Box>
                        Add Project
                      </Menu.Item>

                      <Menu.Separator borderColor="gray.100" my="4px" />

                      <Menu.Item
                        value="sign-out"
                        onClick={handleLogout}
                        px="14px"
                        py="10px"
                        fontSize="sm"
                        color="red.500"
                        _hover={{ bg: 'red.50' }}
                        cursor="pointer"
                        display="flex"
                        alignItems="center"
                        gap="10px"
                      >
                        <Box>
                          <LuLogOut size={15} />
                        </Box>
                        Sign Out
                      </Menu.Item>
                    </Menu.Content>
                  </Menu.Positioner>
                </Portal>
              </Menu.Root>
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
