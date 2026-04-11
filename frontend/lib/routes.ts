export function profilePath(username: string): string {
  return `/profile/${encodeURIComponent(username)}`;
}

export function profileEditPath(username: string): string {
  return `${profilePath(username)}/edit`;
}

export function projectPath(slug: string): string {
  return `/projects/${encodeURIComponent(slug)}`;
}

export function projectEditPath(slug: string): string {
  return `${projectPath(slug)}/edit`;
}
