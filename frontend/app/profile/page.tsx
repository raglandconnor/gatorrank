'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
import { Navbar } from '@/components/Navbar';
import { AcademicInfoCard } from '@/components/AcademicInfoCard';
import { RoleBadge } from '@/components/ui/rolebadge';
import { ProfileUserProjects } from '@/components/ProfileUserProjects';
import { useAuth } from '@/components/auth/AuthProvider';
import { getMe } from '@/lib/api/users';
import type { UserPrivate } from '@/lib/api/types/user';

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? '';
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/* ── Extended profile fields not (yet) in the backend ──────── */
interface ExtendedProfile {
  bio: string;
  socials: { github?: string; linkedin?: string; website?: string };
  major: string;
  graduationYear: number;
  courses: string[];
  skills: string[];
}

const EMPTY_EXTENDED: ExtendedProfile = {
  bio: '',
  socials: {},
  major: '',
  graduationYear: 0,
  courses: [],
  skills: [],
};

function loadExtended(userId: string): ExtendedProfile {
  if (typeof window === 'undefined') return EMPTY_EXTENDED;
  try {
    const raw = localStorage.getItem(`gatorrank_profile_ext_${userId}`);
    if (raw)
      return {
        ...EMPTY_EXTENDED,
        ...(JSON.parse(raw) as Partial<ExtendedProfile>),
      };
  } catch {
    // ignore
  }
  return EMPTY_EXTENDED;
}

/* ── SocialLink ─────────────────────────────────────────────── */
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

/* ── Profile view-model ─────────────────────────────────────── */
interface ProfileViewModel {
  apiUser: UserPrivate;
  extended: ExtendedProfile;
}

/* ── Page ───────────────────────────────────────────────────── */
export default function ProfilePage() {
  const router = useRouter();
  const { user: authUser, isReady } = useAuth();
  const [viewModel, setViewModel] = useState<ProfileViewModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isReady) return;
    if (!authUser) {
      router.replace('/login');
      return;
    }

    async function load() {
      try {
        const apiUser = await getMe();
        const extended = loadExtended(apiUser.id);
        setViewModel({ apiUser, extended });
      } catch {
        setError('Could not load your profile. Please try again.');
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [isReady, authUser, router]);

  /* ── Derived display name for AcademicInfoCard ─────────────── */
  const academicProfile = viewModel
    ? {
        name: viewModel.apiUser.full_name ?? viewModel.apiUser.email,
        role: viewModel.apiUser.role as 'student' | 'faculty',
        avatarUrl: viewModel.apiUser.profile_picture_url ?? undefined,
        bio: viewModel.extended.bio,
        socials: viewModel.extended.socials,
        major: viewModel.extended.major,
        graduationYear: viewModel.extended.graduationYear,
        courses: viewModel.extended.courses,
        skills: viewModel.extended.skills,
      }
    : null;

  /* ── Loading state ──────────────────────────────────────────── */
  if (loading || !isReady) {
    return (
      <Box minH="100vh" bg="white">
        <Navbar />
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="lg" color="orange.400" />
        </Flex>
      </Box>
    );
  }

  if (error || !viewModel || !academicProfile) {
    return (
      <Box minH="100vh" bg="white">
        <Navbar />
        <Flex
          justify="center"
          align="center"
          minH="60vh"
          direction="column"
          gap="12px"
        >
          <Text color="gray.600">{error ?? 'Profile unavailable.'}</Text>
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

  const { apiUser, extended } = viewModel;
  const displayName = apiUser.full_name ?? apiUser.email;

  return (
    <Box minH="100vh" bg="white">
      <Navbar />

      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        {/* Profile hero */}
        <HStack gap="24px" mb="40px" align="flex-start">
          {/* Avatar */}
          {apiUser.profile_picture_url ? (
            <img
              src={apiUser.profile_picture_url}
              alt={displayName}
              style={{
                width: '96px',
                height: '96px',
                borderRadius: '50%',
                objectFit: 'cover',
                flexShrink: 0,
                display: 'block',
              }}
            />
          ) : (
            <Flex
              w="96px"
              h="96px"
              borderRadius="full"
              bg="orange.400"
              color="white"
              align="center"
              justify="center"
              fontSize="2xl"
              fontWeight="bold"
              flexShrink={0}
            >
              {getInitials(displayName)}
            </Flex>
          )}

          {/* Info */}
          <VStack align="start" gap="8px" flex={1}>
            {/* Name + role badge */}
            <HStack gap="12px" align="center" flexWrap="wrap">
              <Text
                fontSize="xl"
                fontWeight="bold"
                color="gray.900"
                lineHeight="32px"
              >
                {displayName}
              </Text>
              <RoleBadge role={apiUser.role as 'student' | 'faculty'} />
            </HStack>

            {/* Bio */}
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
                No bio yet — edit your profile to add one.
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

          {/* Action buttons */}
          <HStack gap="12px" flexShrink={0} align="flex-start">
            <Button
              onClick={() => router.push('/profile/edit')}
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
        </HStack>

        {/* Two-column lower section */}
        <Flex gap="24px" align="start">
          {/* Left: Academic Information */}
          <AcademicInfoCard profile={academicProfile} />

          {/* Right: Skills + Projects */}
          <VStack flex={1} align="start" gap="32px" minW={0}>
            {/* Skills */}
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
                  No skills added yet — edit your profile to add skills.
                </Text>
              )}
            </VStack>

            {/* Projects */}
            <ProfileUserProjects userId={apiUser.id} />
          </VStack>
        </Flex>
      </Box>
    </Box>
  );
}
