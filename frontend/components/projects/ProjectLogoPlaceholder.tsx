'use client';

import { Box, VStack } from '@chakra-ui/react';

interface ProjectLogoPlaceholderProps {
  compact?: boolean;
}

export function ProjectLogoPlaceholder({
  compact = false,
}: ProjectLogoPlaceholderProps) {
  return (
    <Box
      w="100%"
      h="100%"
      borderRadius="inherit"
      overflow="hidden"
      bg="linear-gradient(145deg, #fff7ed 0%, #fed7aa 32%, #fdba74 52%, #1d4ed8 100%)"
      position="relative"
    >
      <Box
        position="absolute"
        top={compact ? '-18%' : '-12%'}
        right={compact ? '-10%' : '-6%'}
        w={compact ? '88px' : '120px'}
        h={compact ? '88px' : '120px'}
        borderRadius="full"
        bg="rgba(255, 255, 255, 0.16)"
      />
      <Box
        position="absolute"
        bottom={compact ? '-16%' : '-10%'}
        left={compact ? '-8%' : '-4%'}
        w={compact ? '90px' : '132px'}
        h={compact ? '90px' : '132px'}
        borderRadius="full"
        bg="rgba(29, 78, 216, 0.18)"
      />

      <VStack
        position="relative"
        zIndex={1}
        w="100%"
        h="100%"
        align="center"
        justify="center"
        gap={compact ? '10px' : '12px'}
        px="14px"
      >
        <Box
          w={compact ? '68px' : '84px'}
          h={compact ? '68px' : '84px'}
          borderRadius={compact ? '22px' : '24px'}
          bg="rgba(255,255,255,0.88)"
          border="1px solid"
          borderColor="whiteAlpha.700"
          boxShadow="0 18px 32px rgba(29, 78, 216, 0.18)"
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <Box
            position="relative"
            w={compact ? '34px' : '42px'}
            h={compact ? '38px' : '46px'}
          >
            <Box
              position="absolute"
              insetX="0"
              top="0"
              mx="auto"
              w={compact ? '26px' : '30px'}
              h={compact ? '14px' : '16px'}
              borderRadius="999px"
              bg="orange.400"
            />
            <Box
              insetX="0"
              top={compact ? '10px' : '12px'}
              mx="auto"
              w={compact ? '20px' : '24px'}
              h={compact ? '20px' : '24px'}
              borderRadius={compact ? '9px' : '10px'}
              border="4px solid"
              borderColor="orange.400"
              borderTopWidth="0"
              bg="transparent"
            />
            <Box
              position="absolute"
              left={compact ? '1px' : '2px'}
              bottom={compact ? '3px' : '4px'}
              w={compact ? '10px' : '12px'}
              h={compact ? '14px' : '18px'}
              borderRadius="999px"
              bg="orange.500"
              transform="rotate(-14deg)"
            />
            <Box
              position="absolute"
              right={compact ? '1px' : '2px'}
              bottom={compact ? '3px' : '4px'}
              w={compact ? '10px' : '12px'}
              h={compact ? '14px' : '18px'}
              borderRadius="999px"
              bg="blue.600"
              transform="rotate(14deg)"
            />
          </Box>
        </Box>
      </VStack>
    </Box>
  );
}
