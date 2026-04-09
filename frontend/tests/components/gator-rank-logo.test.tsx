import { screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { GatorRankLogo } from '@/components/layout/GatorRankLogo';
import { renderWithChakra } from '@/tests/utils/render';

describe('GatorRankLogo', () => {
  test('renders linked logo image to home', () => {
    renderWithChakra(<GatorRankLogo size="sm" />);

    const logoImage = screen.getByAltText('GatorRank');
    expect(logoImage).toBeInTheDocument();

    const homeLink = screen.getByRole('link');
    expect(homeLink).toHaveAttribute('href', '/');
  });
});
