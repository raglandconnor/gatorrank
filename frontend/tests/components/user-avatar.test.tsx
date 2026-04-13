import { fireEvent, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { UserAvatar } from '@/components/ui/UserAvatar';
import { renderWithChakra } from '@/tests/utils/render';

describe('UserAvatar', () => {
  test('renders an accessible initials fallback when no image URL is provided', () => {
    renderWithChakra(<UserAvatar name="Avery Hernandez" />);

    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toBeInTheDocument();
    expect(screen.getByText('AH')).toBeInTheDocument();
  });

  test('renders the image when an image URL is provided', () => {
    renderWithChakra(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-13.png"
      />,
    );

    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toHaveAttribute('src', 'https://avatar.gatorrank.mock/user-13.png');
  });

  test('falls back to an accessible initials avatar when the image fails to load', () => {
    renderWithChakra(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-13.png"
      />,
    );

    fireEvent.error(screen.getByRole('img', { name: 'Avery Hernandez' }));

    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toBeInTheDocument();
    expect(screen.getByText('AH')).toBeInTheDocument();
  });

  test('retries rendering when the image URL changes after a failure', () => {
    const { rerender } = renderWithChakra(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-13.png"
      />,
    );

    fireEvent.error(screen.getByRole('img', { name: 'Avery Hernandez' }));
    expect(screen.getByText('AH')).toBeInTheDocument();

    rerender(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-14.png"
      />,
    );

    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toHaveAttribute('src', 'https://avatar.gatorrank.mock/user-14.png');
  });

  test('retries rendering the same image URL after it is cleared and restored', () => {
    const { rerender } = renderWithChakra(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-13.png"
      />,
    );

    fireEvent.error(screen.getByRole('img', { name: 'Avery Hernandez' }));
    expect(screen.getByText('AH')).toBeInTheDocument();

    rerender(<UserAvatar name="Avery Hernandez" imageUrl={null} />);
    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toBeInTheDocument();

    rerender(
      <UserAvatar
        name="Avery Hernandez"
        imageUrl="https://avatar.gatorrank.mock/user-13.png"
      />,
    );

    expect(
      screen.getByRole('img', { name: 'Avery Hernandez' }),
    ).toHaveAttribute('src', 'https://avatar.gatorrank.mock/user-13.png');
  });
});
