import { describe, expect, test } from 'vitest';
import { fitInlineTags } from '@/lib/projects/fitInlineTags';

describe('fitInlineTags', () => {
  test('returns no tags when width is unavailable', () => {
    expect(fitInlineTags(['React', 'TypeScript'], 0, 1)).toEqual([]);
  });

  test('fits only complete tags on a single row', () => {
    const tags = fitInlineTags(['React', 'TypeScript', 'Chakra'], 120, 1);
    expect(tags).toEqual(['React']);
  });

  test('accepts a caller-provided font string for more accurate fitting', () => {
    const tags = fitInlineTags(
      ['React', 'TypeScript', 'Chakra'],
      120,
      1,
      '400 14px "Mona Sans"',
    );

    expect(tags).toEqual(['React']);
  });

  test('fits tags across two rows without partial trailing items', () => {
    const tags = fitInlineTags(
      ['Open source', 'Community', 'Data viz', 'Campus safety'],
      150,
      2,
    );

    expect(tags.length).toBeGreaterThan(0);
    expect(tags).not.toContain(undefined);
    expect(tags[tags.length - 1]).not.toBe('');
  });
});
