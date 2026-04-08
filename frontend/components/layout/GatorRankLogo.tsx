'use client';

import Image from 'next/image';
import NextLink from 'next/link';
import { Box, Link } from '@chakra-ui/react';

type GatorRankLogoProps = {
  /** "sm" for navbar (60px), "md" for auth pages (responsive) */
  size?: 'sm' | 'md';
};

export function GatorRankLogo({ size = 'md' }: GatorRankLogoProps) {
  const isSm = size === 'sm';

  const containerStyle = isSm
    ? {
        position: 'relative' as const,
        width: 60,
        height: 60,
        flexShrink: 0,
        minWidth: 60,
        minHeight: 60,
      }
    : undefined;

  return (
    <Link
      as={NextLink}
      href="/"
      display="inline-block"
      flexShrink={0}
      _hover={{ transform: 'scale(1.08)' }}
      transition="transform 0.2s ease"
    >
      {isSm ? (
        <div style={containerStyle}>
          <Image
            src="/logo.svg"
            alt="GatorRank"
            fill
            sizes="60px"
            style={{ objectFit: 'contain' }}
            priority
          />
        </div>
      ) : (
        <Box
          position="relative"
          width={{ base: '80px', sm: '96px', md: '112px' }}
          height={{ base: '80px', sm: '96px', md: '112px' }}
          flexShrink={0}
        >
          <Image
            src="/logo.svg"
            alt="GatorRank"
            fill
            sizes="(max-width: 640px) 80px, (max-width: 768px) 96px, 112px"
            style={{ objectFit: 'contain' }}
            priority
          />
        </Box>
      )}
    </Link>
  );
}
