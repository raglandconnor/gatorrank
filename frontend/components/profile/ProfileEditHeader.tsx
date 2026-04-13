'use client';

import {
  Box,
  Button,
  HStack,
  Input,
  Text,
  Textarea,
  VStack,
} from '@chakra-ui/react';
import {
  LuCamera,
  LuGithub,
  LuGlobe,
  LuLinkedin,
  LuSave,
  LuX,
} from 'react-icons/lu';
import { RoleBadge } from '@/components/ui/rolebadge';
import { UserAvatar } from '@/components/ui/UserAvatar';

interface ProfileEditHeaderProps {
  avatarPreview: string | null;
  displayName: string;
  name: string;
  bio: string;
  github: string;
  linkedin: string;
  website: string;
  role: 'student' | 'faculty';
  inputBase: Record<string, unknown>;
  saving: boolean;
  onNameChange: (value: string) => void;
  onBioChange: (value: string) => void;
  onGithubChange: (value: string) => void;
  onLinkedinChange: (value: string) => void;
  onWebsiteChange: (value: string) => void;
  onAvatarClick: () => void;
  onCancel: () => void;
  onSave: () => void;
}

export function ProfileEditHeader({
  avatarPreview,
  displayName,
  name,
  bio,
  github,
  linkedin,
  website,
  role,
  inputBase,
  saving,
  onNameChange,
  onBioChange,
  onGithubChange,
  onLinkedinChange,
  onWebsiteChange,
  onAvatarClick,
  onCancel,
  onSave,
}: ProfileEditHeaderProps) {
  return (
    <HStack gap="24px" mb="40px" align="flex-start">
      <Box
        position="relative"
        w="96px"
        h="96px"
        flexShrink={0}
        cursor="pointer"
        onClick={onAvatarClick}
      >
        <UserAvatar
          name={displayName}
          imageUrl={avatarPreview}
          size="96px"
          fontSize="2xl"
        />
        <Box
          position="absolute"
          inset={0}
          borderRadius="full"
          bg="blackAlpha.500"
          display="flex"
          alignItems="center"
          justifyContent="center"
          opacity={0}
          _hover={{ opacity: 1 }}
          transition="opacity 0.15s"
          color="white"
        >
          <LuCamera size={22} />
        </Box>
      </Box>

      <VStack align="start" gap="10px" flex={1} minW={0}>
        <HStack gap="12px" align="center" w="100%" flexWrap="wrap">
          <Input
            value={name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onNameChange(e.target.value)
            }
            placeholder="Your full name"
            {...inputBase}
            fontSize="xl"
            fontWeight="bold"
            h="47px"
            maxW="400px"
            lineHeight="32px"
          />
          <RoleBadge role={role} />
        </HStack>

        <Textarea
          value={bio}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
            onBioChange(e.target.value)
          }
          placeholder="Tell the community about yourself…"
          {...inputBase}
          h="80px"
          py="10px"
          resize="none"
          maxW="640px"
          lineHeight="24px"
        />

        <VStack align="start" gap="8px" w="100%" maxW="576px">
          <HStack gap="10px" w="100%">
            <Box color="gray.500" flexShrink={0}>
              <LuGithub size={18} />
            </Box>
            <Input
              value={github}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onGithubChange(e.target.value)
              }
              placeholder="https://github.com/username"
              {...inputBase}
              h="36px"
            />
          </HStack>

          <HStack gap="10px" w="100%">
            <Box color="gray.500" flexShrink={0}>
              <LuLinkedin size={18} />
            </Box>
            <Input
              value={linkedin}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onLinkedinChange(e.target.value)
              }
              placeholder="https://linkedin.com/in/username"
              {...inputBase}
              h="36px"
            />
          </HStack>

          <HStack gap="10px" w="100%">
            <Box color="gray.500" flexShrink={0}>
              <LuGlobe size={18} />
            </Box>
            <Input
              value={website}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onWebsiteChange(e.target.value)
              }
              placeholder="https://yourwebsite.com"
              {...inputBase}
              h="36px"
            />
          </HStack>
        </VStack>
      </VStack>

      <HStack gap="12px" flexShrink={0} align="flex-start">
        <Button
          onClick={onCancel}
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
          disabled={saving}
        >
          <HStack gap="6px">
            <LuX size={16} />
            <Text>Cancel</Text>
          </HStack>
        </Button>

        <Button
          onClick={onSave}
          bg="orange.400"
          color="white"
          borderRadius="14px"
          h="44px"
          px="20px"
          fontSize="sm"
          fontWeight="normal"
          _hover={{ bg: 'orange.500' }}
          transition="background 0.15s"
          loading={saving}
        >
          <HStack gap="6px">
            <LuSave size={16} />
            <Text>Save Changes</Text>
          </HStack>
        </Button>
      </HStack>
    </HStack>
  );
}
