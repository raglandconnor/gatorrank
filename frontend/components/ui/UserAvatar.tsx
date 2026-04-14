'use client';

import { useState } from 'react';
import { Flex, Image } from '@chakra-ui/react';
import { getInitials } from '@/lib/profile/profileShared';

type ResponsiveValue = string | Partial<Record<string, string>>;

interface UserAvatarProps {
  name: string;
  imageUrl?: string | null;
  size?: ResponsiveValue;
  fontSize?: ResponsiveValue;
}

function AvatarFallback({
  name,
  size,
  fontSize,
}: {
  name: string;
  size: ResponsiveValue;
  fontSize: ResponsiveValue;
}) {
  return (
    <Flex
      role="img"
      aria-label={name}
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

function AvatarImage({
  name,
  imageUrl,
  size,
  fontSize,
}: {
  name: string;
  imageUrl: string;
  size: ResponsiveValue;
  fontSize: ResponsiveValue;
}) {
  const [hasFailed, setHasFailed] = useState(false);

  if (hasFailed) {
    return <AvatarFallback name={name} size={size} fontSize={fontSize} />;
  }

  return (
    <Image
      src={imageUrl}
      alt={name}
      boxSize={size}
      borderRadius="full"
      objectFit="cover"
      flexShrink={0}
      display="block"
      onError={() => setHasFailed(true)}
    />
  );
}

export function UserAvatar({
  name,
  imageUrl,
  size = '40px',
  fontSize = 'sm',
}: UserAvatarProps) {
  if (imageUrl) {
    return (
      <AvatarImage
        key={imageUrl}
        name={name}
        imageUrl={imageUrl}
        size={size}
        fontSize={fontSize}
      />
    );
  }

  return <AvatarFallback name={name} size={size} fontSize={fontSize} />;
}
