import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import ProjectSearchPage from '@/app/projects/search/page';
import { renderWithChakra } from '@/tests/utils/render';
import type { SearchProjectListItem } from '@/lib/api/types/search';

const { pushMock, paramsRef, accessTokenRef, ioInstances } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  paramsRef: { value: new URLSearchParams('q=ai&sort=top') },
  accessTokenRef: { value: 'token-abc' as string | null },
  ioInstances: [] as MockIntersectionObserver[],
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
  useSearchParams: () => paramsRef.value,
}));

vi.mock('@/components/domain/AuthProvider', () => ({
  useAuth: () => ({
    accessToken: accessTokenRef.value,
  }),
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

const searchProjectsMock = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/search', () => ({
  searchProjects: searchProjectsMock,
}));

class MockIntersectionObserver {
  readonly callback: IntersectionObserverCallback;
  observe = vi.fn();
  disconnect = vi.fn();

  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
    ioInstances.push(this);
  }
}

function makeItem(id: string, title: string): SearchProjectListItem {
  return {
    id,
    created_by_id: 'u1',
    title,
    slug: `${title.toLowerCase().replace(/\s+/g, '-')}-${id}`,
    short_description: `${title} summary`,
    long_description: null,
    demo_url: null,
    github_url: null,
    video_url: null,
    timeline_start_date: null,
    timeline_end_date: null,
    vote_count: 10,
    team_size: 2,
    is_group_project: true,
    is_published: true,
    viewer_has_voted: false,
    published_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
    updated_at: '2026-04-01T00:00:00Z',
    categories: [],
    tags: [],
    tech_stack: [],
    members: [],
  };
}

function triggerIntersection(index = 0) {
  const observer = ioInstances[index];
  if (!observer) throw new Error('Observer not initialized');
  observer.callback(
    [{ isIntersecting: true } as IntersectionObserverEntry],
    observer as unknown as IntersectionObserver,
  );
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('ProjectSearchPage', () => {
  beforeEach(() => {
    pushMock.mockReset();
    searchProjectsMock.mockReset();
    paramsRef.value = new URLSearchParams('q=ai&sort=top');
    accessTokenRef.value = 'token-abc';
    ioInstances.length = 0;

    vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
  });

  test('loads initial results using URL params and auth token', async () => {
    searchProjectsMock.mockResolvedValue({
      items: [makeItem('p1', 'AI Helper')],
      next_cursor: null,
    });

    renderWithChakra(<ProjectSearchPage />);

    expect(await screen.findByText('AI Helper')).toBeInTheDocument();
    expect(searchProjectsMock).toHaveBeenCalledWith(
      { q: 'ai', sort: 'top', limit: 20, cursor: undefined },
      'token-abc',
    );
  });

  test('supports unauthenticated context by passing null token', async () => {
    accessTokenRef.value = null;
    searchProjectsMock.mockResolvedValue({ items: [], next_cursor: null });

    renderWithChakra(<ProjectSearchPage />);

    await waitFor(() => {
      expect(searchProjectsMock).toHaveBeenCalledWith(
        { q: 'ai', sort: 'top', limit: 20, cursor: undefined },
        null,
      );
    });
  });

  test('renders empty-state message when no results are found', async () => {
    searchProjectsMock.mockResolvedValue({ items: [], next_cursor: null });

    renderWithChakra(<ProjectSearchPage />);

    expect(
      await screen.findByText('No projects found for "ai".'),
    ).toBeInTheDocument();
  });

  test('updates URL when sort changes', async () => {
    searchProjectsMock.mockResolvedValue({
      items: [makeItem('p1', 'AI Helper')],
      next_cursor: null,
    });

    renderWithChakra(<ProjectSearchPage />);

    await screen.findByText('AI Helper');
    fireEvent.click(screen.getByRole('button', { name: 'Newest' }));

    expect(pushMock).toHaveBeenCalledWith('/projects/search?q=ai&sort=new');
  });

  test('shows error and retries successfully', async () => {
    searchProjectsMock
      .mockRejectedValueOnce(new Error('Search failed due to a server error.'))
      .mockResolvedValueOnce({
        items: [makeItem('p1', 'Retry Winner')],
        next_cursor: null,
      });

    renderWithChakra(<ProjectSearchPage />);

    expect(
      await screen.findByText('Search failed due to a server error.'),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Retry Search' }));

    expect(await screen.findByText('Retry Winner')).toBeInTheDocument();
    expect(searchProjectsMock).toHaveBeenCalledTimes(2);
  });

  test('appends next page on infinite scroll intersection', async () => {
    searchProjectsMock
      .mockResolvedValueOnce({
        items: [makeItem('p1', 'First Page Project')],
        next_cursor: 'cursor-1',
      })
      .mockResolvedValueOnce({
        items: [makeItem('p2', 'Second Page Project')],
        next_cursor: null,
      });

    renderWithChakra(<ProjectSearchPage />);

    expect(await screen.findByText('First Page Project')).toBeInTheDocument();

    await act(async () => {
      triggerIntersection(0);
    });

    expect(await screen.findByText('Second Page Project')).toBeInTheDocument();
    expect(searchProjectsMock).toHaveBeenNthCalledWith(
      2,
      { q: 'ai', sort: 'top', limit: 20, cursor: 'cursor-1' },
      'token-abc',
    );
  });

  test('ignores stale responses when URL query changes quickly', async () => {
    const first = deferred<{
      items: SearchProjectListItem[];
      next_cursor: null;
    }>();
    const second = deferred<{
      items: SearchProjectListItem[];
      next_cursor: null;
    }>();

    searchProjectsMock
      .mockImplementationOnce(() => first.promise)
      .mockImplementationOnce(() => second.promise);

    const { rerender } = renderWithChakra(<ProjectSearchPage />);

    await waitFor(() => expect(searchProjectsMock).toHaveBeenCalledTimes(1));

    paramsRef.value = new URLSearchParams('q=robot&sort=top');
    rerender(<ProjectSearchPage />);

    await waitFor(() => expect(searchProjectsMock).toHaveBeenCalledTimes(2));

    first.resolve({
      items: [makeItem('old', 'Old Query Result')],
      next_cursor: null,
    });
    second.resolve({
      items: [makeItem('new', 'Robot Result')],
      next_cursor: null,
    });

    expect(await screen.findByText('Robot Result')).toBeInTheDocument();
    expect(screen.queryByText('Old Query Result')).not.toBeInTheDocument();
  });

  test('refetches when URL params change (history/back-forward behavior)', async () => {
    searchProjectsMock
      .mockResolvedValueOnce({
        items: [makeItem('p1', 'AI Result')],
        next_cursor: null,
      })
      .mockResolvedValueOnce({
        items: [makeItem('p2', 'Data Result')],
        next_cursor: null,
      });

    const { rerender } = renderWithChakra(<ProjectSearchPage />);

    expect(await screen.findByText('AI Result')).toBeInTheDocument();

    paramsRef.value = new URLSearchParams('q=data&sort=new');
    rerender(<ProjectSearchPage />);

    expect(await screen.findByText('Data Result')).toBeInTheDocument();
    expect(searchProjectsMock).toHaveBeenNthCalledWith(
      2,
      { q: 'data', sort: 'new', limit: 20, cursor: undefined },
      'token-abc',
    );
  });

  test('invalidates pending request when query is cleared', async () => {
    const pending = deferred<{
      items: SearchProjectListItem[];
      next_cursor: null;
    }>();

    searchProjectsMock.mockImplementationOnce(() => pending.promise);

    const { rerender } = renderWithChakra(<ProjectSearchPage />);
    await waitFor(() => expect(searchProjectsMock).toHaveBeenCalledTimes(1));

    paramsRef.value = new URLSearchParams('sort=top');
    rerender(<ProjectSearchPage />);

    expect(
      await screen.findByText('Enter a keyword to search projects.'),
    ).toBeInTheDocument();

    pending.resolve({
      items: [makeItem('stale', 'Stale Result')],
      next_cursor: null,
    });

    await waitFor(() => {
      expect(screen.queryByText('Stale Result')).not.toBeInTheDocument();
    });
  });
});
