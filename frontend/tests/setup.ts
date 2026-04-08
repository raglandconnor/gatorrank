import React from 'react';
import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

vi.mock('next/image', () => ({
  default: (props: Record<string, unknown>) => {
    const imgProps = { ...props };
    delete imgProps.fill;
    delete imgProps.priority;
    return React.createElement('img', imgProps);
  },
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: Record<string, unknown>) => {
    const normalizedHref =
      typeof href === 'string' ? href : href == null ? '' : String(href);

    return React.createElement(
      'a',
      { ...props, href: normalizedHref },
      children as React.ReactNode,
    );
  },
}));
