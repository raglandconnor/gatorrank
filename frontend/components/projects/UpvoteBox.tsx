'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Box, Button, Text } from '@chakra-ui/react';
import { LuChevronUp } from 'react-icons/lu';
import { useProjectVote } from '@/hooks/useProjectVote';

export function UpvoteBox({
  projectId,
  votes,
  viewerHasVoted = false,
}: {
  projectId: string;
  votes: number;
  viewerHasVoted?: boolean;
}) {
  const { isVoted, voteCount, toggleVote } = useProjectVote({
    projectId,
    initialVoteCount: votes,
    initialViewerHasVoted: viewerHasVoted,
  });

  return (
    <motion.div
      whileTap={{ scale: 1.2, y: -3 }}
      style={{ display: 'contents' }}
    >
      <Button
        type="button"
        variant="plain"
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        p="0"
        gap="8px"
        w={{ base: '88px', md: '108px' }}
        minW={{ base: '88px', md: '108px' }}
        h={{ base: '88px', md: '108px' }}
        overflow="hidden"
        bg={isVoted ? 'orange.50' : 'white'}
        border="2px solid"
        borderColor={isVoted ? 'orange.400' : 'orange.200'}
        borderRadius="12px"
        userSelect="none"
        _hover={{ bg: isVoted ? 'orange.100' : 'orange.50' }}
        _focusVisible={{
          borderColor: 'orange.400',
          boxShadow: '0 0 0 3px rgba(251,146,60,0.35)',
        }}
        transition="background 0.15s, border-color 0.15s, box-shadow 0.15s"
        onClick={() => void toggleVote()}
        aria-label="Upvote"
        aria-pressed={isVoted}
      >
        <Box color={isVoted ? 'orange.500' : 'gray.800'}>
          <LuChevronUp size={24} />
        </Box>
        <Box position="relative" h="24px" w="100%" overflow="hidden">
          <AnimatePresence mode="sync" initial={false}>
            <motion.span
              key={voteCount}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -10, opacity: 0 }}
              transition={{ duration: 0.15 }}
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.2rem',
                fontWeight: 700,
                lineHeight: '24px',
                color: isVoted ? 'rgb(234,88,12)' : 'rgb(17,24,39)',
              }}
            >
              {voteCount}
            </motion.span>
          </AnimatePresence>
        </Box>
        <Text
          fontSize="xs"
          letterSpacing="0.08em"
          color={isVoted ? 'orange.600' : 'gray.600'}
          lineHeight="14px"
        >
          UPVOTE
        </Text>
      </Button>
    </motion.div>
  );
}
