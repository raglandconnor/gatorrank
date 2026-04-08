import type { Project } from '@/data/mock-projects';
import type { ProjectListItem } from '@/lib/api/types/project';

export function mapProjectListItemToCardProject(
  item: ProjectListItem,
): Project {
  return {
    id: item.id,
    name: item.title,
    description: item.short_description,
    tags: item.tags.map((tag) => tag.name),
    votes: item.vote_count,
    // Comments are not returned by current list endpoint.
    comments: 0,
  };
}

export function mapProjectListItemsToCardProjects(
  items: ProjectListItem[],
): Project[] {
  return items.map(mapProjectListItemToCardProject);
}
