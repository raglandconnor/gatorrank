import { expect, test } from '@playwright/test';

test('navbar search routes to results, supports sort, and opens a result', async ({
  page,
}) => {
  await page.route('**/api/v1/projects/search**', async (route) => {
    const url = new URL(route.request().url());
    const sort = url.searchParams.get('sort') ?? 'top';
    const q = url.searchParams.get('q') ?? '';

    const topPayload = {
      items: [
        {
          id: 'p-top-1',
          created_by_id: 'u1',
          title: `Top ${q}`,
          slug: 'top-q',
          short_description: 'Top sorted result',
          long_description: null,
          demo_url: null,
          github_url: null,
          video_url: null,
          timeline_start_date: null,
          timeline_end_date: null,
          vote_count: 99,
          team_size: 3,
          is_group_project: true,
          is_published: true,
          viewer_has_voted: false,
          published_at: '2026-04-01T00:00:00Z',
          created_at: '2026-04-01T00:00:00Z',
          updated_at: '2026-04-01T00:00:00Z',
          categories: [],
          tags: [],
          tech_stack: [],
          members: [],
        },
      ],
      next_cursor: null,
    };

    const newPayload = {
      items: [
        {
          id: 'p-new-1',
          created_by_id: 'u1',
          title: `New ${q}`,
          slug: 'new-q',
          short_description: 'New sorted result',
          long_description: null,
          demo_url: null,
          github_url: null,
          video_url: null,
          timeline_start_date: null,
          timeline_end_date: null,
          vote_count: 10,
          team_size: 2,
          is_group_project: true,
          is_published: true,
          viewer_has_voted: false,
          published_at: '2026-04-01T00:00:00Z',
          created_at: '2026-04-01T00:00:00Z',
          updated_at: '2026-04-01T00:00:00Z',
          categories: [],
          tags: [],
          tech_stack: [],
          members: [],
        },
      ],
      next_cursor: null,
    };

    const body = sort === 'new' ? newPayload : topPayload;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(body),
    });
  });

  await page.route('**/api/v1/projects/*', async (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.endsWith('/api/v1/projects/p-new-1')) {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'p-new-1',
        created_by_id: 'u1',
        title: 'New ranking',
        slug: 'new-ranking',
        short_description: 'New sorted result',
        long_description: 'Project details loaded from backend endpoint.',
        demo_url: null,
        github_url: 'https://github.com/example/new-ranking',
        video_url: null,
        timeline_start_date: null,
        timeline_end_date: null,
        vote_count: 10,
        team_size: 2,
        is_group_project: true,
        is_published: true,
        viewer_has_voted: false,
        published_at: '2026-04-01T00:00:00Z',
        created_at: '2026-04-01T00:00:00Z',
        updated_at: '2026-04-01T00:00:00Z',
        categories: [],
        tags: [],
        tech_stack: [],
        members: [
          {
            user_id: 'u1',
            username: 'owner_one',
            role: 'owner',
            full_name: 'Owner One',
            profile_picture_url: null,
          },
        ],
      }),
    });
  });

  await page.goto('/');

  await page.getByPlaceholder('Search projects').fill('ranking');
  await page.getByRole('button', { name: 'Search projects' }).click();

  await expect(page).toHaveURL(/\/projects\/search\?q=ranking&sort=top/);
  await expect(page.getByText('Top ranking')).toBeVisible();

  await page.getByRole('button', { name: 'New' }).click();

  await expect(page).toHaveURL(/\/projects\/search\?q=ranking&sort=new/);
  await expect(page.getByText('New ranking')).toBeVisible();

  await page.getByRole('link', { name: /New ranking/ }).click();
  await expect(page).toHaveURL(/\/projects\/p-new-1/);
  await expect(page.getByText('About This Project')).toBeVisible();
  await expect(
    page.getByText('Project details loaded from backend endpoint.'),
  ).toBeVisible();
});
