import { createSystem, defaultConfig, defineConfig } from '@chakra-ui/react';

const config = defineConfig({
  theme: {
    tokens: {
      fonts: {
        body: { value: 'var(--font-mona-sans), system-ui, sans-serif' },
        heading: { value: 'var(--font-mona-sans), system-ui, sans-serif' },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
