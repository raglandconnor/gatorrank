'use client';

import { useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Box, Flex, HStack, Text } from '@chakra-ui/react';
import { LuTag } from 'react-icons/lu';
import { fitInlineTags } from '@/lib/projects/fitInlineTags';

interface ProjectInlineTagsProps {
  tags: string[];
  maxRows: 1 | 2;
}

export function ProjectInlineTags({ tags, maxRows }: ProjectInlineTagsProps) {
  const measureRef = useRef<HTMLDivElement | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [containerFont, setContainerFont] = useState('');

  useLayoutEffect(() => {
    const node = measureRef.current;
    if (!node) return;

    const updateWidth = () => {
      const nextWidth = node.clientWidth || node.getBoundingClientRect().width;
      setContainerWidth(Math.floor(nextWidth));

      const styles = window.getComputedStyle(node);
      const font =
        styles.font && styles.font !== 'normal'
          ? styles.font
          : `${styles.fontWeight} ${styles.fontSize} ${styles.fontFamily}`;
      setContainerFont(font.trim());
    };

    updateWidth();
    const frame = window.requestAnimationFrame(updateWidth);

    if (typeof ResizeObserver === 'undefined') {
      return () => {
        window.cancelAnimationFrame(frame);
      };
    }

    const observer = new ResizeObserver(() => {
      updateWidth();
    });
    observer.observe(node);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [tags, maxRows]);

  const visibleTags = useMemo(
    () =>
      containerWidth > 0
        ? fitInlineTags(tags, containerWidth, maxRows, containerFont)
        : tags,
    [tags, containerWidth, maxRows, containerFont],
  );

  if (!tags.length) {
    return <Box ref={measureRef} w="100%" minW={0} h="0" overflow="hidden" />;
  }

  const rowHeight = 24;
  const maxHeight = `${rowHeight * maxRows}px`;

  const content = visibleTags.map((tag, index) => (
    <Flex key={tag} align="center" minW={0} flexShrink={0}>
      <Text
        fontSize="sm"
        color="gray.800"
        lineHeight="24px"
        whiteSpace={maxRows === 1 ? 'nowrap' : 'normal'}
        _hover={{
          textDecoration: 'underline',
          textUnderlineOffset: '2px',
        }}
      >
        {tag}
      </Text>
      {index < visibleTags.length - 1 ? (
        <Box
          w="4px"
          h="4px"
          borderRadius="full"
          bg="gray.500"
          mx="9px"
          flexShrink={0}
        />
      ) : null}
    </Flex>
  ));

  return (
    <Flex w="100%" minW={0} align="flex-start" gap="8px">
      <Box color="gray.800" mt="5px" flexShrink={0}>
        <LuTag size={13} />
      </Box>
      <Box
        ref={measureRef}
        minW={0}
        w="100%"
        overflow="hidden"
        maxH={maxHeight}
      >
        {maxRows === 1 ? (
          <HStack
            gap={0}
            align="center"
            minW={0}
            overflow="hidden"
            h={maxHeight}
          >
            {content}
          </HStack>
        ) : (
          <Flex
            wrap="wrap"
            gapX="0px"
            gapY="0px"
            align="center"
            maxH={maxHeight}
            overflow="hidden"
          >
            {content}
          </Flex>
        )}
      </Box>
    </Flex>
  );
}
