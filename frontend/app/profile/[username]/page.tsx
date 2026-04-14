'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  Link as ChakraLink,
  Spinner,
} from '@chakra-ui/react';
import {
  LuPencil,
  LuPlus,
  LuGithub,
  LuLinkedin,
  LuGlobe,
} from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import { AcademicInfoCard } from '@/components/profile/AcademicInfoCard';
import { RoleBadge } from '@/components/ui/rolebadge';
import { ProfileUserProjects } from '@/components/profile/ProfileUserProjects';
import { useAuth } from '@/components/domain/AuthProvider';
import { getUserPublic, getUserPublicByUsername } from '@/lib/api/users';
import type { ExtendedProfile } from '@/lib/profile/profileShared';
import {
  EMPTY_EXTENDED,
  loadExtendedProfile as loadExtended,
} from '@/lib/profile/profileShared';
import { isUuid } from '@/lib/profileSlug';
import { profileEditPath, profilePath } from '@/lib/routes';
import type { UserPublic } from '@/lib/api/types/user';
import { UserAvatar } from '@/components/ui/UserAvatar';

function SocialLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <ChakraLink
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      w="36px"
      h="36px"
      bg="gray.100"
      borderRadius="full"
      display="flex"
      alignItems="center"
      justifyContent="center"
      color="gray.700"
      _hover={{ bg: 'gray.200', color: 'gray.900' }}
      transition="background 0.15s, color 0.15s"
    >
      {icon}
    </ChakraLink>
  );
}

type LoadState =
  | { status: 'loading' }
  | { status: 'notfound' }
  | { status: 'error'; message: string }
  | { status: 'ready'; publicUser: UserPublic; extended: ExtendedProfile };

export default function ProfileUserPage() {
  const router = useRouter();
  const { username } = useParams<{ username: string }>();
  const { user: authUser, isReady } = useAuth();
  const [state, setState] = useState<LoadState>({ status: 'loading' });

  // null = projects not yet loaded; -1 = error; >= 0 = item count
  const [projectCount, setProjectCount] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      setState({ status: 'loading' });
      setProjectCount(null);

      try {
        const publicUser = isUuid(username)
          ? await getUserPublic(username)
          : await getUserPublicByUsername(username);
        if (publicUser.username !== username) {
          router.replace(profilePath(publicUser.username));
        }
        const extended =
          authUser?.id === publicUser.id
            ? loadExtended(publicUser.id)
            : EMPTY_EXTENDED;
        setState({ status: 'ready', publicUser, extended });
      } catch (err) {
        const isNotFound =
          err instanceof Error &&
          (err as Error & { status?: number }).status === 404;
        if (isNotFound) {
          setState({ status: 'notfound' });
        } else {
          setState({
            status: 'error',
            message: 'Could not load profile. Please try again.',
          });
        }
      }
    }

    void load();
  }, [authUser?.id, router, username]);

  const handleProjectsLoaded = useCallback((count: number) => {
    setProjectCount(count);
  }, []);

  if (state.status === 'loading') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="lg" color="orange.400" />
        </Flex>
      </Box>
    );
  }

  if (state.status === 'notfound') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex
          justify="center"
          align="center"
          minH="60vh"
          direction="column"
          gap="12px"
        >
          <Text color="gray.600">This profile does not exist.</Text>
          <Button
            bg="orange.400"
            color="white"
            _hover={{ bg: 'orange.500' }}
            onClick={() => router.push('/')}
          >
            Go home
          </Button>
        </Flex>
      </Box>
    );
  }

  if (state.status === 'error') {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex
          justify="center"
          align="center"
          minH="60vh"
          direction="column"
          gap="12px"
        >
          <Text color="gray.600">{state.message}</Text>
          <Button
            bg="orange.400"
            color="white"
            _hover={{ bg: 'orange.500' }}
            onClick={() => router.refresh()}
          >
            Try again
          </Button>
        </Flex>
      </Box>
    );
  }

  const { publicUser, extended } = state;
  const isOwn = isReady && authUser?.id === publicUser.id;
  const displayName =
    publicUser.full_name ??
    (isOwn && authUser?.email ? authUser.email : 'GatorRank User');

  const academicProfile = {
    name: displayName,
    role: publicUser.role as 'student' | 'faculty',
    avatarUrl: publicUser.profile_picture_url ?? undefined,
    bio: extended.bio,
    socials: extended.socials,
    major: extended.major,
    graduationYear: extended.graduationYear,
    courses: extended.courses,
    skills: extended.skills,
  };

  const extendedIsEmpty =
    !extended.bio &&
    extended.skills.length === 0 &&
    !extended.major &&
    extended.graduationYear <= 0 &&
    extended.courses.length === 0;

  // Projects have finished loading with zero items (not an error)
  const projectsLoadedEmpty = projectCount !== null && projectCount === 0;

  // Owner: show complete-your-profile banner when everything is empty
  const showOwnerBanner = isOwn && extendedIsEmpty && projectsLoadedEmpty;

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />

      <Box
        px={{ base: '16px', md: '24px', lg: '36px' }}
        pt="32px"
        pb="64px"
        maxW="1280px"
        mx="auto"
      >
        {/* Profile hero */}
        <Flex
          gap={{ base: '16px', md: '24px' }}
          mb="40px"
          align="flex-start"
          direction={{ base: 'column', md: 'row' }}
        >
          <UserAvatar
            name={displayName}
            imageUrl={publicUser.profile_picture_url}
            size="96px"
            fontSize="2xl"
          />

          <VStack align="start" gap="8px" flex={1} minW={0}>
            <HStack gap="12px" align="center" flexWrap="wrap">
              <Text
                fontSize="xl"
                fontWeight="bold"
                color="gray.900"
                lineHeight="32px"
              >
                {displayName}
              </Text>
              <RoleBadge role={publicUser.role as 'student' | 'faculty'} />
            </HStack>

            {/* Bio: filled content shown for everyone; empty hint shown for everyone */}
            {extended.bio ? (
              <Text
                fontSize="sm"
                color="gray.600"
                lineHeight="24px"
                maxW="640px"
              >
                {extended.bio}
              </Text>
            ) : (
              <Text
                fontSize="sm"
                color="gray.400"
                lineHeight="24px"
                maxW="640px"
              >
                {isOwn
                  ? 'No bio yet — edit your profile to add one.'
                  : 'No bio added yet.'}
              </Text>
            )}

            {/* Social links */}
            <HStack gap="8px" mt="4px">
              {extended.socials.github && (
                <SocialLink
                  href={extended.socials.github}
                  icon={<LuGithub size={18} />}
                  label="GitHub"
                />
              )}
              {extended.socials.linkedin && (
                <SocialLink
                  href={extended.socials.linkedin}
                  icon={<LuLinkedin size={18} />}
                  label="LinkedIn"
                />
              )}
              {extended.socials.website && (
                <SocialLink
                  href={extended.socials.website}
                  icon={<LuGlobe size={18} />}
                  label="Website"
                />
              )}
            </HStack>
          </VStack>

          {isOwn && (
            <HStack
              gap="12px"
              flexShrink={0}
              align="flex-start"
              flexWrap="wrap"
            >
              <Button
                onClick={() =>
                  router.push(profileEditPath(publicUser.username))
                }
                variant="outline"
                border="1px solid"
                borderColor="orange.400"
                borderRadius="14px"
                h="44px"
                px="20px"
                fontSize="sm"
                color="gray.900"
                bg="white"
                _hover={{ bg: 'orange.50' }}
                transition="background 0.15s"
              >
                <HStack gap="6px">
                  <LuPencil size={16} />
                  <Text>Edit Profile</Text>
                </HStack>
              </Button>

              <Button
                bg="orange.400"
                color="white"
                borderRadius="14px"
                h="44px"
                px="20px"
                fontSize="sm"
                fontWeight="normal"
                _hover={{ bg: 'orange.500' }}
                transition="background 0.15s"
                onClick={() => router.push('/projects/create')}
              >
                <HStack gap="6px">
                  <LuPlus size={16} />
                  <Text>Add Project</Text>
                </HStack>
              </Button>
            </HStack>
          )}
        </Flex>

        {/* Owner: complete-your-profile banner */}
        {showOwnerBanner && (
          <Box
            bg="orange.50"
            border="1px solid"
            borderColor="orange.200"
            borderRadius="13px"
            p="24px"
            mb="32px"
          >
            <VStack align="start" gap="12px">
              <Text fontSize="sm" fontWeight="medium" color="gray.700">
                Your profile is looking sparse — fill in your bio, skills, and
                academic info so others can learn about you.
              </Text>
              <Button
                size="sm"
                bg="orange.400"
                color="white"
                borderRadius="10px"
                _hover={{ bg: 'orange.500' }}
                onClick={() =>
                  router.push(profileEditPath(publicUser.username))
                }
              >
                Complete your profile
              </Button>
            </VStack>
          </Box>
        )}

        <Flex
          gap="24px"
          align="start"
          direction={{ base: 'column', md: 'row' }}
        >
          <Box w={{ base: '100%', md: '344px' }} flexShrink={0}>
            <AcademicInfoCard profile={academicProfile} />
          </Box>

          <VStack flex={1} align="start" gap="32px" minW={0}>
            {/* Skills: always shown */}
            <VStack align="start" gap="16px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Skills
              </Text>
              {extended.skills.length > 0 ? (
                <Wrap gap="8px">
                  {extended.skills.map((skill: string) => (
                    <Box
                      key={skill}
                      bg="rgba(251,146,60,0.1)"
                      border="1.6px solid"
                      borderColor="orange.400"
                      borderRadius="10px"
                      px="16px"
                      py="8px"
                    >
                      <Text fontSize="sm" color="orange.400" lineHeight="24px">
                        {skill}
                      </Text>
                    </Box>
                  ))}
                </Wrap>
              ) : (
                <Text fontSize="sm" color="gray.400" lineHeight="24px">
                  {isOwn
                    ? 'No skills added yet — edit your profile to add skills.'
                    : 'No skills added yet.'}
                </Text>
              )}
            </VStack>

            {/* Projects — always mounted to ensure onLoadComplete fires */}
            <ProfileUserProjects
              username={publicUser.username}
              isOwn={isOwn}
              onLoadComplete={handleProjectsLoaded}
            />
          </VStack>
        </Flex>
      </Box>
    </Box>
  );
}
