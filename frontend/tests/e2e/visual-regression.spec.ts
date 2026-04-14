import { expect, test } from '@playwright/test';

const projectPayload = {
  items: [
    {
      id: 'p-vr-1',
      created_by_id: 'u-vr-1',
      title: 'Visual Regression Project',
      slug: 'vr-project',
      short_description: 'A mock project for visual regression testing',
      long_description: null,
      demo_url: null,
      github_url: null,
      video_url: null,
      timeline_start_date: null,
      timeline_end_date: null,
      vote_count: 42,
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

function mockProjectRoutes(page: import('@playwright/test').Page) {
  return page.route('**/api/v1/projects**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(projectPayload),
    });
  });
}

test.describe('visual regression - public pages', () => {
  test('home page', async ({ page }) => {
    await mockProjectRoutes(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot('home.png', { fullPage: true });
  });

  test('login page', async ({ page }) => {
    await page.goto('/login');
    await expect(
      page.getByRole('heading', { name: 'Welcome Back' }),
    ).toBeVisible();
    await expect(page).toHaveScreenshot('login.png', { fullPage: true });
  });

  test('signup page', async ({ page }) => {
    await page.goto('/signup');
    await expect(
      page.getByRole('heading', { name: 'Display Your Projects to the World' }),
    ).toBeVisible();
    await expect(page).toHaveScreenshot('signup.png', { fullPage: true });
  });

  test('search results page', async ({ page }) => {
    await page.route('**/api/v1/projects/search**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(projectPayload),
      });
    });
    await page.goto('/projects/search?q=test&sort=top');
    await expect(page.getByText('Visual Regression Project')).toBeVisible();
    await expect(page).toHaveScreenshot('search.png', { fullPage: true });
  });

  test('top projects page', async ({ page }) => {
    await mockProjectRoutes(page);
    await page.goto('/projects/top/trending-this-month');
    await expect(
      page.getByText('Trending UF Projects This Month'),
    ).toBeVisible();
    await expect(page).toHaveScreenshot('top-projects.png', {
      fullPage: true,
    });
  });
});
