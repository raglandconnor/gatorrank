'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Button,
  Container,
  Flex,
  HStack,
  Spinner,
  Text,
  VStack,
} from '@chakra-ui/react';
import { Navbar } from '@/components/Navbar';
import { SearchResultRow } from '@/components/projects/SearchResultRow';
import { useAuth } from '@/components/auth/AuthProvider';
import { searchProjects } from '@/lib/api/search';
import type { SearchProjectListItem, SearchSort } from '@/lib/api/types/search';

const PAGE_SIZE = 20;

function normalizeSort(value: string | null): SearchSort {
  return value === 'new' ? 'new' : 'top';
}

export default function ProjectSearchPage() {
  const router = useRouter();
  const params = useSearchParams();
  const { accessToken } = useAuth();

  const query = (params.get('q') ?? '').trim();
  const sort = normalizeSort(params.get('sort'));

  const [items, setItems] = useState<SearchProjectListItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingInitial, setLoadingInitial] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const requestIdRef = useRef(0);

  const hasQuery = query.length > 0;
  const hasMore = nextCursor !== null;

  const updateUrl = useCallback(
    (nextQuery: string, nextSort: SearchSort) => {
      const nextParams = new URLSearchParams();
      if (nextQuery) nextParams.set('q', nextQuery);
      nextParams.set('sort', nextSort);
      router.push(`/projects/search?${nextParams.toString()}`);
    },
    [router],
  );

  const loadPage = useCallback(
    async (cursor?: string) => {
      const requestId = ++requestIdRef.current;

      if (!hasQuery) {
        setItems([]);
        setNextCursor(null);
        setError(null);
        setLoadingInitial(false);
        setLoadingMore(false);
        return;
      }
      if (cursor) {
        setLoadingMore(true);
      } else {
        setLoadingInitial(true);
      }

      try {
        const response = await searchProjects(
          {
            q: query,
            sort,
            limit: PAGE_SIZE,
            cursor,
          },
          accessToken,
        );

        if (requestId !== requestIdRef.current) return;

        setItems((prev) =>
          cursor ? [...prev, ...response.items] : response.items,
        );
        setNextCursor(response.next_cursor);
        setError(null);
      } catch (err) {
        if (requestId !== requestIdRef.current) return;
        const message =
          err instanceof Error ? err.message : 'Failed to load search results.';
        setError(message);
        if (!cursor) {
          setItems([]);
          setNextCursor(null);
        }
      } finally {
        if (requestId !== requestIdRef.current) return;
        if (cursor) {
          setLoadingMore(false);
        } else {
          setLoadingInitial(false);
        }
      }
    },
    [accessToken, hasQuery, query, sort],
  );

  useEffect(() => {
    void loadPage();
  }, [loadPage]);

  useEffect(() => {
    if (
      !hasMore ||
      loadingInitial ||
      loadingMore ||
      !sentinelRef.current ||
      error
    ) {
      return;
    }

    const node = sentinelRef.current;
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) return;
        if (!nextCursor) return;
        void loadPage(nextCursor);
      },
      { rootMargin: '220px' },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [error, hasMore, loadPage, loadingInitial, loadingMore, nextCursor]);

  const resultSummary = useMemo(() => {
    if (!hasQuery) return 'Enter a keyword to search projects.';
    if (loadingInitial) return 'Searching projects...';
    if (error) return error;
    if (items.length === 0) return `No projects found for "${query}".`;
    return `${items.length} result${items.length === 1 ? '' : 's'} for "${query}"`;
  }, [error, hasQuery, items.length, loadingInitial, query]);

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />

      <Container maxW="1080px" px={{ base: '20px', md: '36px' }} py="32px">
        <VStack align="stretch" gap="20px">
          <HStack
            ml={{ base: 0, md: 'auto' }}
            bg="gray.100"
            borderRadius="10px"
            p="4px"
            gap="4px"
            w="fit-content"
          >
            <Button
              type="button"
              size="sm"
              borderRadius="8px"
              bg={sort === 'top' ? 'white' : 'transparent'}
              color={sort === 'top' ? 'gray.900' : 'gray.600'}
              onClick={() => updateUrl(query, 'top')}
              _hover={{ bg: 'white' }}
            >
              Top
            </Button>
            <Button
              type="button"
              size="sm"
              borderRadius="8px"
              bg={sort === 'new' ? 'white' : 'transparent'}
              color={sort === 'new' ? 'gray.900' : 'gray.600'}
              onClick={() => updateUrl(query, 'new')}
              _hover={{ bg: 'white' }}
            >
              New
            </Button>
          </HStack>

          <Text fontSize="sm" color={error ? 'red.500' : 'gray.600'}>
            {resultSummary}
          </Text>

          {loadingInitial ? (
            <Flex justify="center" py="40px">
              <Spinner size="lg" color="orange.400" />
            </Flex>
          ) : (
            <VStack align="stretch" gap="12px">
              {items.map((project) => (
                <SearchResultRow key={project.id} project={project} />
              ))}
            </VStack>
          )}

          {!loadingInitial && hasMore && !error && (
            <Box ref={sentinelRef} h="1px" w="100%" />
          )}

          {loadingMore && (
            <Flex justify="center" py="12px">
              <Spinner size="md" color="orange.400" />
            </Flex>
          )}

          {!loadingInitial && error && hasQuery && (
            <Flex>
              <Button
                type="button"
                onClick={() => void loadPage()}
                bg="gray.900"
                color="white"
                borderRadius="10px"
                h="40px"
                px="16px"
                _hover={{ bg: 'gray.700' }}
              >
                Retry Search
              </Button>
            </Flex>
          )}
        </VStack>
      </Container>
    </Box>
  );
}
