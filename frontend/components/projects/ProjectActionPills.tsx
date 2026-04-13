'use client';

import type { MouseEventHandler } from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { LuChevronUp, LuMessageSquare } from 'react-icons/lu';

export function CommentPill({
  count,
  onClick,
  ariaLabel,
}: {
  count: number;
  onClick?: MouseEventHandler<HTMLElement>;
  ariaLabel?: string;
}) {
  return (
    <Box
      data-project-card-action="true"
      as="button"
      display="flex"
      alignItems="center"
      justifyContent="center"
      gap="7px"
      bg="white"
      border="1.6px solid"
      borderColor="orange.200"
      borderRadius="12px"
      pl="13px"
      pr="10px"
      h="42px"
      minW="76px"
      cursor={onClick ? 'pointer' : 'default'}
      _hover={onClick ? { bg: 'orange.50' } : undefined}
      transition="background 0.15s, border-color 0.15s"
      onClick={onClick}
      aria-label={ariaLabel ?? `${count} comments`}
    >
      <Flex
        w="15px"
        minW="15px"
        h="15px"
        align="center"
        justify="center"
        color="gray.700"
      >
        <LuMessageSquare size={15} />
      </Flex>
      <Flex w="18px" minW="18px" align="center" justify="center">
        <Text
          fontSize="sm"
          fontWeight="normal"
          color="gray.700"
          lineHeight="20px"
        >
          {count}
        </Text>
      </Flex>
    </Box>
  );
}

export function VotePill({
  count,
  active = false,
  pending = false,
  onClick,
  ariaLabel,
}: {
  count: number;
  active?: boolean;
  pending?: boolean;
  onClick?: MouseEventHandler<HTMLElement>;
  ariaLabel?: string;
}) {
  return (
    <Box
      data-project-card-action="true"
      as="button"
      display="flex"
      alignItems="center"
      justifyContent="center"
      gap="2px"
      bg={active ? 'orange.50' : 'white'}
      border="1.6px solid"
      borderColor={active ? 'orange.400' : 'orange.200'}
      borderRadius="12px"
      pl="12px"
      pr="5px"
      h="42px"
      minW="76px"
      cursor={pending ? 'wait' : 'pointer'}
      opacity={pending ? 0.85 : 1}
      _hover={{ bg: active ? 'orange.100' : 'orange.50' }}
      transition="background 0.15s, border-color 0.15s, opacity 0.15s"
      onClick={onClick}
      aria-label={ariaLabel}
      aria-disabled={pending}
      aria-pressed={active}
    >
      <Flex
        w="14px"
        minW="14px"
        h="14px"
        align="center"
        justify="center"
        color={active ? 'orange.500' : 'gray.700'}
      >
        <LuChevronUp size={15} />
      </Flex>
      <Box position="relative" h="20px" w="28px" overflow="hidden">
        <AnimatePresence mode="sync" initial={false}>
          <motion.span
            key={count}
            initial={{ y: 8, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -8, opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.875rem',
              fontWeight: 400,
              lineHeight: '20px',
              color: active ? 'rgb(234,88,12)' : 'rgb(55,65,81)',
            }}
          >
            {count}
          </motion.span>
        </AnimatePresence>
      </Box>
    </Box>
  );
}
