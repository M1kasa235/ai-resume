import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/auth/login');
    
    await expect(page).toHaveTitle(/登录/);
    await expect(page.getByRole('heading', { name: '登录' })).toBeVisible();
    await expect(page.getByPlaceholder('用户名')).toBeVisible();
    await expect(page.getByPlaceholder('密码')).toBeVisible();
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/auth/login');
    
    await page.getByRole('button', { name: '登录' }).click();
    
    await expect(page.getByText('请输入用户名')).toBeVisible();
    await expect(page.getByText('请输入密码')).toBeVisible();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/auth/login');
    
    await page.getByText('还没有账号？').click();
    
    await expect(page).toHaveURL('/auth/register');
    await expect(page.getByRole('heading', { name: '注册' })).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test('should display dashboard after login', async ({ page }) => {
    // Mock successful login
    await page.goto('/auth/login');
    await page.fill('input[placeholder="用户名"]', 'testuser');
    await page.fill('input[placeholder="密码"]', 'password123');
    await page.getByRole('button', { name: '登录' }).click();
    
    // Wait for navigation to dashboard
    await page.waitForURL('/dashboard');
    
    await expect(page.getByRole('heading', { name: '仪表盘' })).toBeVisible();
    await expect(page.getByText('投递总数')).toBeVisible();
    await expect(page.getByText('AI面试')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate between different pages', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test navigation to jobs page
    await page.getByRole('link', { name: '岗位列表' }).click();
    await expect(page).toHaveURL('/jobs');
    await expect(page.getByRole('heading', { name: '岗位搜索' })).toBeVisible();
    
    // Test navigation to questions page
    await page.getByRole('link', { name: '题库' }).click();
    await expect(page).toHaveURL('/questions');
    await expect(page.getByRole('heading', { name: '题库练习' })).toBeVisible();
    
    // Test navigation to workbench page
    await page.getByRole('link', { name: '工作台' }).click();
    await expect(page).toHaveURL('/workbench');
    await expect(page.getByRole('heading', { name: '工作台' })).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('should display mobile menu on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Check that mobile menu is visible
    await expect(page.getByRole('button', { name: '菜单' })).toBeVisible();
    
    // Test mobile navigation
    await page.getByRole('button', { name: '菜单' }).click();
    await page.getByRole('link', { name: '岗位列表' }).click();
    
    await expect(page).toHaveURL('/jobs');
  });
});

test.describe('Error Handling', () => {
  test('should display 404 page for non-existent routes', async ({ page }) => {
    await page.goto('/non-existent-page');
    
    await expect(page.getByRole('heading', { name: '404' })).toBeVisible();
    await expect(page.getByText('页面不存在')).toBeVisible();
    await expect(page.getByRole('button', { name: '返回首页' })).toBeVisible();
  });
});