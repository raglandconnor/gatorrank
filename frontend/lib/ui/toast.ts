/**
 * Thin wrappers around the Chakra toaster that apply consistent defaults:
 *   - closable: true by default — spread `opts` after so callers may pass
 *     closable: false when a non-dismissible toast is required.
 *   - duration: 6 s for errors/warnings; 4 s for success/info
 *
 * Import these helpers instead of `toaster` directly so callers do not
 * have to repeat options.
 */
import type { ToastOptions } from '@chakra-ui/react';
import { toaster } from '@/components/ui/toaster';

type Options = Omit<ToastOptions, 'type'>;

const base = (opts: Options): Options => ({
  closable: true,
  ...opts,
});

export const toast = {
  success: (opts: Options) =>
    toaster.success({ duration: 4000, ...base(opts) }),
  error: (opts: Options) => toaster.error({ duration: 6000, ...base(opts) }),
  warning: (opts: Options) =>
    toaster.warning({ duration: 6000, ...base(opts) }),
  info: (opts: Options) => toaster.info({ duration: 4000, ...base(opts) }),
};
