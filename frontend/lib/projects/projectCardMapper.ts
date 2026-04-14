import type { Project } from '@/types/project';
import type { ProjectListItem } from '@/lib/api/types/project';

export function mapProjectListItemToCardProject(
  item: ProjectListItem,
): Project {
  return {
    id: item.id,
    name: item.title,
    slug: item.slug,
    description: item.short_description,
    categories: item.categories.map((c) => c.name),
    tags: item.tags.map((tag) => tag.name),
    tech_stack: item.tech_stack.map((t) => t.name),
    votes: item.vote_count,
    viewerHasVoted: item.viewer_has_voted,
    // Comments are not returned by current list endpoint.
    comments: 0,
  };
}

export function mapProjectListItemsToCardProjects(
  items: ProjectListItem[],
): Project[] {
  return items.map(mapProjectListItemToCardProject);
}
