'use client';

import { FormEvent, useMemo } from 'react';
import { GatorRankLogo } from '@/components/layout/GatorRankLogo';
import { useAuth } from '@/components/domain/AuthProvider';
import {
  Box,
  HStack,
  Text,
  Flex,
  Link,
  Menu,
  Portal,
  Input,
  Button,
} from '@chakra-ui/react';
import NextLink from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import {
  LuChevronDown,
  LuUser,
  LuPlus,
  LuLogOut,
  LuSearch,
} from 'react-icons/lu';
import { profilePath } from '@/lib/routes';
import { UserAvatar } from '@/components/ui/UserAvatar';

export function Navbar() {
  const { user, isReady, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const navSearchDefault =
    pathname === '/projects/search' ? (searchParams.get('q') ?? '') : '';

  const showSearch = useMemo(() => {
    if (!pathname) return true;
    if (pathname === '/projects/create') return false;
    if (pathname === '/projects/edit') return false;
    if (pathname === '/profile/edit') return false;
    if (/^\/projects\/[^/]+\/edit$/.test(pathname)) return false;
    if (/^\/profile\/[^/]+\/edit$/.test(pathname)) return false;
    return true;
  }, [pathname]);

  const handleLogout = async () => {
    await logout();
    router.push('/login?signedOut=1');
  };

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const normalized = String(formData.get('q') ?? '').trim();
    if (!normalized) return;
    const params = new URLSearchParams();
    params.set('q', normalized);
    params.set('sort', 'top');
    router.push(`/projects/search?${params.toString()}`);
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
        <Flex h="100%" align="center" justify="space-between" gap="20px">
          {/* Left side: logo + nav links */}
          <HStack gap="32px" align="center">
            <GatorRankLogo size="sm" />
          </HStack>

          {showSearch ? (
            <Box flex="1" maxW="520px" key={`${pathname}-${navSearchDefault}`}>
              <form onSubmit={handleSearchSubmit}>
                <HStack gap="8px" align="center">
                  <Input
                    name="q"
                    defaultValue={navSearchDefault}
                    placeholder="Search projects"
                    bg="white"
                    border="1px solid"
                    borderColor="gray.300"
                    borderRadius="12px"
                    h="42px"
                    minW="0"
                  />
                  <Button
                    type="submit"
                    aria-label="Search projects"
                    h="42px"
                    minW="42px"
                    px="12px"
                    borderRadius="12px"
                    bg="gray.900"
                    color="white"
                    _hover={{ bg: 'gray.700' }}
                  >
                    <LuSearch size={16} />
                  </Button>
                </HStack>
              </form>
            </Box>
          ) : (
            <Box flex="1" />
          )}

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
                    <UserAvatar
                      name={user.full_name ?? user.email}
                      imageUrl={user.profile_picture_url}
                      size="38px"
                      fontSize="sm"
                    />
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
                        onClick={() => router.push(profilePath(user.username))}
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
