'use client';

import { Box, Flex, Text, VStack } from '@chakra-ui/react';
import { motion } from 'framer-motion';

interface FeatureLoadingStateProps {
  title: string;
  description: string;
  icon: React.ReactNode;
}

export function FeatureLoadingState({
  title,
  description,
  icon,
}: FeatureLoadingStateProps) {
  return (
    <Flex minH="68vh" align="center" justify="center">
      <VStack
        gap="18px"
        px={{ base: '28px', md: '40px' }}
        py={{ base: '30px', md: '38px' }}
        bg="white"
        borderRadius="24px"
        border="1px solid"
        borderColor="orange.100"
        boxShadow="0 18px 50px rgba(15,23,42,0.08)"
        textAlign="center"
      >
        <Box position="relative" w="82px" h="82px">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.4, repeat: Infinity, ease: 'linear' }}
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '9999px',
              border: '3px solid rgba(251,191,36,0.22)',
              borderTopColor: '#f59e0b',
            }}
          />
          <motion.div
            animate={{ scale: [0.94, 1.04, 0.94] }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{
              position: 'absolute',
              inset: '12px',
              borderRadius: '9999px',
              background:
                'linear-gradient(135deg, rgba(251,191,36,0.18), rgba(249,115,22,0.28))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box color="orange.500">{icon}</Box>
          </motion.div>
        </Box>

        <VStack gap="6px">
          <Text fontSize="lg" fontWeight="bold" color="gray.900">
            {title}
          </Text>
          <Text fontSize="sm" color="gray.600" maxW="320px" lineHeight="22px">
            {description}
          </Text>
        </VStack>
      </VStack>
    </Flex>
  );
}
