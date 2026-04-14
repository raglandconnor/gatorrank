import { expect, test } from '@playwright/test';

test('home renders sections and allows navigating to login', async ({
  page,
}, testInfo) => {
  test.skip(
    testInfo.project.name === 'mobile' || testInfo.project.name === 'tablet',
    'Functional smoke test — desktop only',
  );
  await page.route('**/api/v1/projects**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'p-home-1',
            created_by_id: 'u-home-1',
            title: 'Home Project',
            slug: 'home-project',
            short_description: 'Home project description',
            long_description: null,
            demo_url: null,
            github_url: null,
            video_url: null,
            timeline_start_date: null,
            timeline_end_date: null,
            vote_count: 3,
            team_size: 1,
            is_group_project: false,
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
      }),
    });
  });

  await page.goto('/');

  await expect(page.getByText('Top Overall UF Projects')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Sign Up' })).toBeVisible();

  const loginLink = page.getByRole('link', { name: 'Log In' });
  await expect(loginLink).toBeVisible();
  await loginLink.click();

  await expect(page).toHaveURL(/\/login/);
  await expect(
    page.getByRole('heading', { name: 'Welcome Back' }),
  ).toBeVisible();
});
