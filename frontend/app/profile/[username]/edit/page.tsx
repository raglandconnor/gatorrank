'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Input,
  Textarea,
  Spinner,
} from '@chakra-ui/react';
import {
  LuX,
  LuSave,
  LuGithub,
  LuLinkedin,
  LuGlobe,
  LuMail,
  LuCamera,
} from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import { toast } from '@/lib/ui/toast';
import { RoleBadge } from '@/components/ui/rolebadge';
import { getMe, patchMe } from '@/lib/api/users';
import type { AuthUser } from '@/lib/api/types/auth';
import type { UserPrivate } from '@/lib/api/types/user';
import { useAuth } from '@/components/domain/AuthProvider';
import { loadExtendedProfile as loadExtended } from '@/lib/profile/profileShared';
import { isUuid } from '@/lib/profileSlug';
import { profilePath, profileEditPath } from '@/lib/routes';
import { UserAvatar } from '@/components/ui/UserAvatar';

const inputBase = {
  border: '1px solid',
  borderColor: 'gray.300',
  borderRadius: '10px',
  px: '12px',
  bg: 'white',
  fontSize: 'sm',
  color: 'gray.900',
  w: '100%',
  outline: 'none',
  _focus: { borderColor: 'orange.400' },
} as const;

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <Text fontSize="sm" color="gray.500" lineHeight="24px">
      {children}
    </Text>
  );
}

function ComingSoonTag() {
  return (
    <Text
      as="span"
      fontSize="xs"
      color="orange.600"
      bg="orange.50"
      border="1px solid"
      borderColor="orange.200"
      borderRadius="999px"
      px="8px"
      py="1px"
      lineHeight="18px"
    >
      Coming soon
    </Text>
  );
}

function FieldLabelWithComingSoon({ children }: { children: React.ReactNode }) {
  return (
    <HStack gap="8px">
      <FieldLabel>{children}</FieldLabel>
      <ComingSoonTag />
    </HStack>
  );
}

function DisabledFieldHint() {
  return (
    <Text fontSize="xs" color="gray.500" lineHeight="20px">
      This field is not editable yet.
    </Text>
  );
}

function ComingSoonBlock({
  children,
  mb = '0px',
}: {
  children: React.ReactNode;
  mb?: string;
}) {
  return (
    <VStack
      align="start"
      gap="6px"
      w="100%"
      mb={mb}
      opacity={0.5}
      filter="grayscale(20%)"
      bg="gray.50"
      border="1px dashed"
      borderColor="gray.300"
      borderRadius="10px"
      p="10px"
    >
      {children}
      <DisabledFieldHint />
    </VStack>
  );
}

export default function EditProfilePage() {
  const router = useRouter();
  const { username } = useParams<{ username: string }>();
  const { user: authUser, isReady, updateCachedUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  /** Tracks blob: URLs from file picks only (not remote profile_picture_url). */
  const avatarObjectUrlRef = useRef<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiUser, setApiUser] = useState<UserPrivate | null>(null);

  const [name, setName] = useState('');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [profilePictureUrl, setProfilePictureUrl] = useState('');

  const [bio, setBio] = useState('');
  const [github, setGithub] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [website, setWebsite] = useState('');

  useEffect(() => {
    if (!isReady) return;

    if (!authUser) {
      router.replace('/login');
      return;
    }

    async function load() {
      try {
        const user = await getMe();
        if (isUuid(username)) {
          if (username !== user.id) {
            router.replace(profileEditPath(user.username));
            return;
          }
          router.replace(profileEditPath(user.username));
          return;
        } else if (username !== user.username) {
          router.replace(profileEditPath(user.username));
          return;
        }
        setApiUser(user);
        setName(user.full_name ?? '');
        avatarObjectUrlRef.current = null;
        setProfilePictureUrl(user.profile_picture_url ?? '');
        setAvatarPreview(user.profile_picture_url ?? null);

        const ext = loadExtended(user.id);
        setBio(ext.bio);
        setGithub(ext.socials.github ?? '');
        setLinkedin(ext.socials.linkedin ?? '');
        setWebsite(ext.socials.website ?? '');
      } catch {
        toast.error({
          title: 'Could not load profile',
          description: 'Please try again.',
        });
        router.push('/profile');
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [authUser, isReady, router, username]);

  useEffect(() => {
    return () => {
      if (avatarObjectUrlRef.current) {
        URL.revokeObjectURL(avatarObjectUrlRef.current);
      }
    };
  }, []);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const MAX_SIZE_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_SIZE_BYTES) {
      e.target.value = '';
      if (fileInputRef.current) fileInputRef.current.value = '';
      toast.error({
        id: String(Date.now()),
        title: 'Image too large',
        description: 'Please choose a file smaller than 5MB.',
        duration: 3000,
      });
      return;
    }

    e.target.value = '';
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (avatarObjectUrlRef.current) {
      URL.revokeObjectURL(avatarObjectUrlRef.current);
    }
    const url = URL.createObjectURL(file);
    avatarObjectUrlRef.current = url;
    setAvatarPreview(url);
  };

  const handleSave = async () => {
    if (!apiUser) return;
    const trimmedName = name.trim();
    const normalizedProfilePictureUrl = profilePictureUrl.trim();
    const originalName = apiUser.full_name ?? '';
    const originalProfilePictureUrl = apiUser.profile_picture_url ?? '';

    const payload: { full_name?: string; profile_picture_url?: string | null } =
      {};
    if (trimmedName && trimmedName !== originalName) {
      payload.full_name = trimmedName;
    }
    if (normalizedProfilePictureUrl !== originalProfilePictureUrl) {
      payload.profile_picture_url = normalizedProfilePictureUrl || null;
    }
    if (Object.keys(payload).length === 0) {
      toast.info({
        title: 'No changes to save',
      });
      return;
    }

    setSaving(true);
    try {
      const updated = await patchMe(payload);

      const nextAuth: AuthUser = {
        id: updated.id,
        email: updated.email,
        username: updated.username,
        role: updated.role,
        full_name: updated.full_name,
        profile_picture_url: updated.profile_picture_url,
      };
      updateCachedUser(nextAuth);

      toast.success({
        title: 'Profile saved',
        description: 'Your changes have been saved.',
      });
      router.push(profilePath(updated.username));
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Could not save profile.';
      toast.error({ title: 'Save failed', description: message });
    } finally {
      setSaving(false);
    }
  };

  if (loading || !isReady) {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="lg" color="orange.400" />
        </Flex>
      </Box>
    );
  }

  if (!apiUser) return null;

  const displayName = apiUser.full_name ?? apiUser.email;

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleAvatarChange}
      />

      <Box
        px={{ base: '16px', md: '24px', lg: '36px' }}
        pt="32px"
        pb="64px"
        maxW="1280px"
        mx="auto"
      >
        <Flex
          gap={{ base: '16px', md: '24px' }}
          mb="40px"
          align="flex-start"
          direction={{ base: 'column', md: 'row' }}
          flexWrap="wrap"
        >
          <Box
            position="relative"
            w={{ base: '72px', md: '96px' }}
            h={{ base: '72px', md: '96px' }}
            flexShrink={0}
            cursor="pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <UserAvatar
              name={displayName}
              imageUrl={avatarPreview}
              size={{ base: '72px', md: '96px' }}
              fontSize={{ base: 'xl', md: '2xl' }}
            />
            <Box
              position="absolute"
              inset={0}
              borderRadius="full"
              bg="blackAlpha.500"
              display="flex"
              alignItems="center"
              justifyContent="center"
              opacity={{ base: 0.6, md: 0 }}
              _hover={{ opacity: 1 }}
              transition="opacity 0.15s"
              color="white"
            >
              <LuCamera size={22} />
            </Box>
          </Box>

          {/* Info VStack */}
          <VStack align="start" gap="10px" flex={1} minW={0}>
            <HStack gap="12px" align="center" w="100%" flexWrap="wrap">
              <Input
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setName(e.target.value)
                }
                placeholder="Your full name"
                {...inputBase}
                fontSize="xl"
                fontWeight="bold"
                h="47px"
                maxW="400px"
                lineHeight="32px"
              />
              <RoleBadge role={apiUser.role as 'student' | 'faculty'} />
            </HStack>

            <ComingSoonBlock mb="2px">
              <FieldLabelWithComingSoon>Bio</FieldLabelWithComingSoon>
              <Textarea
                value={bio}
                placeholder="Tell the community about yourself…"
                {...inputBase}
                h="80px"
                py="10px"
                resize="none"
                maxW="640px"
                lineHeight="24px"
                disabled
                opacity={0.7}
              />
            </ComingSoonBlock>

            <ComingSoonBlock>
              <FieldLabelWithComingSoon>Social Links</FieldLabelWithComingSoon>
              <VStack align="start" gap="8px" w="100%" maxW="576px">
                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuGithub size={18} />
                  </Box>
                  <Input
                    value={github}
                    placeholder="https://github.com/username"
                    {...inputBase}
                    h="36px"
                    disabled
                    opacity={0.7}
                  />
                </HStack>

                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuLinkedin size={18} />
                  </Box>
                  <Input
                    value={linkedin}
                    placeholder="https://linkedin.com/in/username"
                    {...inputBase}
                    h="36px"
                    disabled
                    opacity={0.7}
                  />
                </HStack>

                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuGlobe size={18} />
                  </Box>
                  <Input
                    value={website}
                    placeholder="https://yourwebsite.com"
                    {...inputBase}
                    h="36px"
                    disabled
                    opacity={0.7}
                  />
                </HStack>
              </VStack>
            </ComingSoonBlock>
          </VStack>

          {/* Buttons */}
          <HStack
            gap={{ base: '8px', md: '12px' }}
            flexShrink={0}
            align="flex-start"
            flexWrap="wrap"
          >
            <Button
              onClick={() => router.push(profilePath(apiUser.username))}
              variant="outline"
              border="1px solid"
              borderColor="orange.400"
              borderRadius={{ base: '10px', md: '14px' }}
              h={{ base: '36px', md: '44px' }}
              px={{ base: '14px', md: '20px' }}
              fontSize={{ base: 'xs', md: 'sm' }}
              color="gray.900"
              bg="white"
              _hover={{ bg: 'orange.50' }}
              transition="background 0.15s"
              disabled={saving}
            >
              <HStack gap="6px">
                <LuX size={14} />
                <Text>Cancel</Text>
              </HStack>
            </Button>

            <Button
              onClick={handleSave}
              bg="orange.400"
              color="white"
              borderRadius={{ base: '10px', md: '14px' }}
              h={{ base: '36px', md: '44px' }}
              px={{ base: '14px', md: '20px' }}
              fontSize={{ base: 'xs', md: 'sm' }}
              fontWeight="normal"
              _hover={{ bg: 'orange.500' }}
              transition="background 0.15s"
              loading={saving}
            >
              <HStack gap="6px">
                <LuSave size={14} />
                <Text>Save Changes</Text>
              </HStack>
            </Button>
          </HStack>
        </Flex>

        {/* Account Settings */}
        <Box
          mt="8px"
          bg="gray.100"
          borderRadius="13px"
          p={{ base: '16px', md: '24px' }}
          w="100%"
          maxW="640px"
        >
          <VStack align="start" gap="16px" w="100%">
            <Text
              fontSize="md"
              fontWeight="bold"
              color="gray.900"
              lineHeight="30px"
            >
              Account Settings
            </Text>

            <VStack align="start" gap="4px" w="100%">
              <FieldLabel>Profile Picture URL</FieldLabel>
              <Input
                type="url"
                value={profilePictureUrl}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  const nextUrl = e.target.value;
                  setProfilePictureUrl(nextUrl);
                  setAvatarPreview(nextUrl.trim() || null);
                }}
                placeholder="https://example.com/avatar.jpg"
                {...inputBase}
                h="43px"
              />
            </VStack>

            <VStack align="start" gap="4px" w="100%">
              <FieldLabel>Email Address</FieldLabel>
              <Box position="relative" w="100%">
                <Box
                  position="absolute"
                  left="12px"
                  top="50%"
                  transform="translateY(-50%)"
                  color="gray.400"
                  pointerEvents="none"
                >
                  <LuMail size={16} />
                </Box>
                <Input
                  type="email"
                  value={apiUser.email}
                  readOnly
                  disabled
                  {...inputBase}
                  h="43px"
                  pl="38px"
                  opacity={0.6}
                  cursor="not-allowed"
                />
              </Box>
            </VStack>
          </VStack>
        </Box>
      </Box>
    </Box>
  );
}
