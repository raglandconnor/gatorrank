import { createSystem, defaultConfig, defineConfig } from '@chakra-ui/react';

const config = defineConfig({
  theme: {
    tokens: {
      fonts: {
        body: { value: "'Mona Sans', system-ui, sans-serif" },
        heading: { value: "'Mona Sans', system-ui, sans-serif" },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
