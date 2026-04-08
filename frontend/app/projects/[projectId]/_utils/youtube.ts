export function getYouTubeEmbedUrl(url: string): string | null {
  const trimmed = url.trim();
  if (!trimmed) return null;

  try {
    const parsed = new URL(trimmed);
    const host = parsed.hostname.replace(/^www\./, '').toLowerCase();
    let videoId = '';

    if (host === 'youtu.be') {
      videoId = parsed.pathname.split('/').filter(Boolean)[0] ?? '';
    } else if (host === 'youtube.com' || host === 'm.youtube.com') {
      if (parsed.pathname === '/watch') {
        videoId = parsed.searchParams.get('v') ?? '';
      } else if (parsed.pathname.startsWith('/shorts/')) {
        videoId = parsed.pathname.split('/')[2] ?? '';
      } else if (parsed.pathname.startsWith('/embed/')) {
        videoId = parsed.pathname.split('/')[2] ?? '';
      }
    }

    const VIDEO_ID_REGEX = /^[a-zA-Z0-9_-]{11}$/;
    if (!videoId) return null;
    const normalizedVideoId = videoId.trim();
    if (!VIDEO_ID_REGEX.test(normalizedVideoId)) return null;

    return `https://www.youtube.com/embed/${encodeURIComponent(normalizedVideoId)}`;
  } catch {
    return null;
  }
}
