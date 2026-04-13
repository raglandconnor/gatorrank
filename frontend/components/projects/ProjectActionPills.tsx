'use client';

import type { MouseEventHandler } from 'react';
import { Box, Button, Flex, Text } from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { LuChevronUp, LuMessageSquare } from 'react-icons/lu';

export function CommentPill({
  count,
  onClick,
  ariaLabel,
}: {
  count: number;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  ariaLabel?: string;
}) {
  const content = (
    <>
      <Flex
        w="15px"
        minW="15px"
        h="15px"
        align="center"
        justify="center"
        color="gray.700"
        aria-hidden="true"
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
    </>
  );

  if (!onClick) {
    return (
      <Box
        data-project-card-action="true"
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
      >
        {content}
      </Box>
    );
  }

  return (
    <Button
      data-project-card-action="true"
      type="button"
      variant="plain"
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
      cursor="pointer"
      _hover={{ bg: 'orange.50' }}
      transition="background 0.15s, border-color 0.15s"
      onClick={onClick}
      aria-label={ariaLabel ?? `${count} comments`}
    >
      {content}
    </Button>
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
  onClick?: MouseEventHandler<HTMLButtonElement>;
  ariaLabel?: string;
}) {
  return (
    <Button
      data-project-card-action="true"
      type="button"
      variant="plain"
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
      cursor={pending ? 'not-allowed' : 'pointer'}
      opacity={pending ? 0.85 : 1}
      _hover={pending ? undefined : { bg: active ? 'orange.100' : 'orange.50' }}
      transition="background 0.15s, border-color 0.15s, opacity 0.15s"
      onClick={pending ? undefined : onClick}
      disabled={pending}
      aria-label={ariaLabel}
      aria-pressed={active}
    >
      <Flex
        w="14px"
        minW="14px"
        h="14px"
        align="center"
        justify="center"
        color={active ? 'orange.500' : 'gray.700'}
        aria-hidden="true"
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
    </Button>
  );
}
