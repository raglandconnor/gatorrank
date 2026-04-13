'use client';

import { useState } from 'react';
import { Flex, Image } from '@chakra-ui/react';
import { getInitials } from '@/lib/profile/profileShared';

interface UserAvatarProps {
  name: string;
  imageUrl?: string | null;
  size?: string;
  fontSize?: string;
}

export function UserAvatar({
  name,
  imageUrl,
  size = '40px',
  fontSize = 'sm',
}: UserAvatarProps) {
  const [failedImageUrl, setFailedImageUrl] = useState<string | null>(null);

  if (imageUrl && failedImageUrl !== imageUrl) {
    return (
      <Image
        src={imageUrl}
        alt={name}
        boxSize={size}
        borderRadius="full"
        objectFit="cover"
        flexShrink={0}
        display="block"
        onError={() => setFailedImageUrl(imageUrl)}
      />
    );
  }

  return (
    <Flex
      boxSize={size}
      borderRadius="full"
      bg="orange.400"
      color="white"
      align="center"
      justify="center"
      fontSize={fontSize}
      fontWeight="bold"
      flexShrink={0}
    >
      {getInitials(name)}
    </Flex>
  );
}
