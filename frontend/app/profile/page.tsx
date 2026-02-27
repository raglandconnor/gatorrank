'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  SimpleGrid,
  Avatar,
  Link as ChakraLink,
} from '@chakra-ui/react';
import {
  LuPencil,
  LuPlus,
  LuGraduationCap,
  LuBookOpen,
  LuGithub,
  LuLinkedin,
  LuGlobe,
} from 'react-icons/lu';
import { Navbar } from '@/components/Navbar';
import { AcademicInfoCard } from '@/components/AcademicInfoCard';
import { ProfileProjectCard } from '@/components/ProfileProjectCard';
import { mockProfile, mockProfileProjects } from '@/data/mock-profile';

function RoleBadge({ role }: { role: 'student' | 'faculty' }) {
  const Icon = role === 'faculty' ? LuBookOpen : LuGraduationCap;
  const label = role === 'faculty' ? 'Faculty' : 'Student';

  return (
    <HStack
      gap="6px"
      bg="rgba(251,146,60,0.1)"
      border="1.6px solid"
      borderColor="orange.400"
      borderRadius="full"
      px="12px"
      py="4px"
      display="inline-flex"
    >
      <Box color="orange.400">
        <Icon size={14} />
      </Box>
      <Text fontSize="xs" color="orange.400" fontWeight="medium">
        {label}
      </Text>
    </HStack>
  );
}

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

export default function ProfilePage() {
  const router = useRouter();
  const getSavedProfile = () => {
    try {
      const raw = localStorage.getItem('gatorrank_profile');
      if (raw) return JSON.parse(raw);
    } catch {
      // ignore
    }
    return mockProfile;
  };

  const [profile, setProfile] = useState(() =>
    typeof window !== 'undefined' ? getSavedProfile() : mockProfile,
  );
  const projects = mockProfileProjects;

  return (
    <Box minH="100vh" bg="white">
      <Navbar />

      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        {/* Profile hero */}
        <HStack gap="24px" mb="40px" align="flex-start">
          {/* Avatar */}
          <Avatar.Root
            w="96px"
            h="96px"
            flexShrink={0}
            borderRadius="full"
            overflow="hidden"
          >
            <Avatar.Fallback
              name={profile.name}
              bg="gray.300"
              color="gray.700"
              fontSize="xl"
              fontWeight="bold"
            />
            {profile.avatarUrl && <Avatar.Image src={profile.avatarUrl} />}
          </Avatar.Root>

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
                {profile.name}
              </Text>
              <RoleBadge role={profile.role} />
            </HStack>

            {/* Bio */}
            <Text fontSize="sm" color="gray.600" lineHeight="24px" maxW="640px">
              {profile.bio}
            </Text>

            {/* Social links */}
            <HStack gap="8px" mt="4px">
              {profile.socials.github && (
                <SocialLink
                  href={profile.socials.github}
                  icon={<LuGithub size={18} />}
                  label="GitHub"
                />
              )}
              {profile.socials.linkedin && (
                <SocialLink
                  href={profile.socials.linkedin}
                  icon={<LuLinkedin size={18} />}
                  label="LinkedIn"
                />
              )}
              {profile.socials.website && (
                <SocialLink
                  href={profile.socials.website}
                  icon={<LuGlobe size={18} />}
                  label="Website"
                />
              )}
            </HStack>
          </VStack>

          {/* Action buttons — pinned right, top-aligned */}
          <HStack gap="12px" flexShrink={0} align="flex-start">
            {/* Use router.push to avoid nested anchor issues */}
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
          <AcademicInfoCard profile={profile} />

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
              <Wrap gap="8px">
                {profile.skills.map((skill: string) => (
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
            </VStack>

            {/* Projects */}
            <VStack align="start" gap="16px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Projects
              </Text>
              <SimpleGrid columns={3} gap="16px" w="100%">
                {projects.map((project) => (
                  <ProfileProjectCard key={project.id} project={project} />
                ))}
              </SimpleGrid>
            </VStack>
          </VStack>
        </Flex>
      </Box>
    </Box>
  );
}
