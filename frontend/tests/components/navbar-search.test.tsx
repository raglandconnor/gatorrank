import { fireEvent, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { Navbar } from '@/components/layout/Navbar';
import { renderWithChakra } from '@/tests/utils/render';

const { pushMock, pathnameRef, searchParamsRef } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  pathnameRef: { value: '/' },
  searchParamsRef: { value: new URLSearchParams() },
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
  usePathname: () => pathnameRef.value,
  useSearchParams: () => searchParamsRef.value,
}));

vi.mock('@/components/domain/AuthProvider', () => ({
  useAuth: () => ({
    user: null,
    isReady: true,
    logout: vi.fn(),
  }),
}));

describe('Navbar search', () => {
  beforeEach(() => {
    pushMock.mockReset();
    pathnameRef.value = '/';
    searchParamsRef.value = new URLSearchParams();
  });

  test('submits trimmed query and routes to search page', () => {
    renderWithChakra(<Navbar />);

    const input = screen.getByPlaceholderText('Search projects');
    fireEvent.change(input, { target: { value: '  ai tools  ' } });

    const form = input.closest('form');
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    expect(pushMock).toHaveBeenCalledWith(
      '/projects/search?q=ai+tools&sort=top',
    );
  });

  test('does not route when query is empty', () => {
    renderWithChakra(<Navbar />);

    const input = screen.getByPlaceholderText('Search projects');
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.submit(input.closest('form')!);

    expect(pushMock).not.toHaveBeenCalled();
  });

  test('hides navbar search on create/edit routes', () => {
    pathnameRef.value = '/projects/create';
    const { rerender } = renderWithChakra(<Navbar />);

    expect(
      screen.queryByPlaceholderText('Search projects'),
    ).not.toBeInTheDocument();

    pathnameRef.value = '/profile/123/edit';
    rerender(<Navbar />);
    expect(
      screen.queryByPlaceholderText('Search projects'),
    ).not.toBeInTheDocument();
  });

  test('prefills query on search route', () => {
    pathnameRef.value = '/projects/search';
    searchParamsRef.value = new URLSearchParams('q=ml+ranking&sort=new');

    renderWithChakra(<Navbar />);

    const input = screen.getByPlaceholderText(
      'Search projects',
    ) as HTMLInputElement;
    expect(input.value).toBe('ml ranking');
  });
});
