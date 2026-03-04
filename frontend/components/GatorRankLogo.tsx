'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import NextLink from 'next/link';
import { Box, Link } from '@chakra-ui/react';

export function GatorRankLogo() {
  return (
    <Link as={NextLink} href="/" display="block">
      <motion.div
        whileHover={{ scale: 1.08 }}
        transition={{ duration: 0.2 }}
        style={{ display: 'inline-block' }}
      >
        <Box
          position="relative"
          width={{ base: '100px', sm: '120px', md: '140px' }}
          height={{ base: '100px', sm: '120px', md: '140px' }}
          flexShrink={0}
        >
          <Image
            src="/logo.svg"
            alt="GatorRank"
            fill
            sizes="(max-width: 640px) 100px, (max-width: 768px) 120px, 140px"
            style={{ objectFit: 'contain' }}
            priority
          />
        </Box>
      </motion.div>
    </Link>
  );
}
