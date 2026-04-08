// @vitest-environment node
import { describe, expect, test } from 'vitest';
import type { ProjectListItem } from '@/lib/api/types/project';
import {
  mapProjectListItemToCardProject,
  mapProjectListItemsToCardProjects,
} from '@/lib/projects/projectCardMapper';

/** Minimal valid `ProjectListItem` for mapper tests (shape must stay aligned with API). */
function listItemFixture(
  overrides: Partial<ProjectListItem> = {},
): ProjectListItem {
  return {
    id: 'proj-1',
    created_by_id: 'user-1',
    title: 'Swampfolio',
    slug: 'swampfolio',
    short_description: 'Portfolio for UF engineers.',
    long_description: null,
    demo_url: null,
    github_url: null,
    video_url: null,
    timeline_start_date: null,
    timeline_end_date: null,
    vote_count: 42,
    team_size: 1,
    is_group_project: false,
    is_published: true,
    viewer_has_voted: false,
    published_at: '2026-03-15T12:00:00Z',
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-03-15T12:00:00Z',
    categories: [],
    tags: [
      { id: 't1', name: 'Web' },
      { id: 't2', name: 'Career' },
    ],
    tech_stack: [],
    members: [],
    ...overrides,
  };
}

describe('projectCardMapper', () => {
  test('maps tag objects to name strings in order', () => {
    const item = listItemFixture({
      tags: [
        { id: 'a', name: 'iOS' },
        { id: 'b', name: 'Education' },
        { id: 'c', name: 'Open Source' },
      ],
    });

    const card = mapProjectListItemToCardProject(item);

    expect(card.tags).toEqual(['iOS', 'Education', 'Open Source']);
  });

  test('sets comments to 0 (list DTO has no comment count)', () => {
    const item = listItemFixture({ vote_count: 100 });

    const card = mapProjectListItemToCardProject(item);

    expect(card.comments).toBe(0);
  });

  test('maps core list fields onto card shape', () => {
    const item = listItemFixture({
      id: 'uuid-string',
      title: 'GatorMap',
      short_description: 'Campus maps.',
      vote_count: 9,
      tags: [{ id: 'x', name: 'Maps' }],
    });

    expect(mapProjectListItemToCardProject(item)).toEqual({
      id: 'uuid-string',
      name: 'GatorMap',
      description: 'Campus maps.',
      tags: ['Maps'],
      votes: 9,
      comments: 0,
    });
  });

  test('mapProjectListItemsToCardProjects maps each item', () => {
    const items = [
      listItemFixture({ id: '1', title: 'A', tags: [{ id: 't', name: 'X' }] }),
      listItemFixture({ id: '2', title: 'B', tags: [] }),
    ];

    const cards = mapProjectListItemsToCardProjects(items);

    expect(cards).toHaveLength(2);
    expect(cards[0]?.name).toBe('A');
    expect(cards[0]?.tags).toEqual(['X']);
    expect(cards[1]?.comments).toBe(0);
  });
});
