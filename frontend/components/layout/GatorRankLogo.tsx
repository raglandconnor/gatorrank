'use client';

import Image from 'next/image';
import NextLink from 'next/link';
import { Box, Link } from '@chakra-ui/react';
import type { BoxProps } from '@chakra-ui/react';

type GatorRankLogoProps = {
  /** "sm" for the navbar variant, "md" for auth pages (responsive) */
  size?: 'sm' | 'md';
  /** Optional explicit width override for cases where the logo needs a custom display box */
  width?: BoxProps['width'];
  /** Optional explicit height override for cases where the logo needs a custom display box */
  height?: BoxProps['height'];
  /** Optional sizes override for Next.js image optimization */
  imageSizes?: string;
};

export function GatorRankLogo({
  size = 'md',
  width,
  height,
  imageSizes,
}: GatorRankLogoProps) {
  const isSm = size === 'sm';

  // "sm" maps to the navbar treatment, which can still use a larger box than the
  // older 60px asset sizing when the surrounding layout allows it.
  const resolvedWidth = width ?? (isSm ? '100px' : { base: '80px', sm: '96px', md: '120px' });
  const resolvedHeight =
    height ?? (isSm ? '100px' : { base: '80px', sm: '96px', md: '120px' });
  const resolvedSizes =
    imageSizes ??
    (isSm ? '100px' : '(max-width: 640px) 80px, (max-width: 768px) 100px, 120px');

  return (
    <Link
      as={NextLink}
      href="/"
      display="inline-block"
      flexShrink={0}
      _hover={{ transform: 'scale(1.08)' }}
      transition="transform 0.2s ease"
    >
      <Box
        position="relative"
        width={resolvedWidth}
        height={resolvedHeight}
        minW={resolvedWidth}
        minH={resolvedHeight}
        flexShrink={0}
      >
        <Image
          src="/logo.svg"
          alt="GatorRank"
          fill
          sizes={resolvedSizes}
          style={{ objectFit: 'contain' }}
          priority
        />
      </Box>
    </Link>
  );
}
