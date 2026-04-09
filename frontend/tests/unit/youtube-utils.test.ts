import { describe, expect, test } from 'vitest';
import { getYouTubeEmbedUrl } from '@/lib/projects/youtube';

describe('getYouTubeEmbedUrl', () => {
  test('parses youtu.be links', () => {
    expect(getYouTubeEmbedUrl('https://youtu.be/dQw4w9WgXcQ')).toBe(
      'https://www.youtube.com/embed/dQw4w9WgXcQ',
    );
  });

  test('parses watch links', () => {
    expect(
      getYouTubeEmbedUrl('https://www.youtube.com/watch?v=dQw4w9WgXcQ'),
    ).toBe('https://www.youtube.com/embed/dQw4w9WgXcQ');
  });

  test('rejects non-youtube links', () => {
    expect(getYouTubeEmbedUrl('https://example.com/watch?v=dQw4w9WgXcQ')).toBe(
      null,
    );
  });

  test('rejects invalid video ids', () => {
    expect(getYouTubeEmbedUrl('https://youtu.be/not-valid-id')).toBe(null);
  });
});
