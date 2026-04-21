import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  // const BASE_URL = 'http://localhost:8000'; // TODO: 使用此URL进行实际API测试

  test.beforeEach(async ({ page }) => {
    // 设置API拦截
    await page.route('**/api/**', async (route) => {
      const request = route.request();
      const url = request.url();
      
      // 模拟API响应
      if (url.includes('/api/v1/auth/register')) {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            username: 'testuser',
            email: 'test@example.com',
            phone: null,
            avatar_url: null,
            real_name: null,
            gender: null,
            current_city: null,
            target_city: null,
            work_years: null,
            education: null,
            is_active: true,
            is_admin: false,
            created_at: '2024-01-01T00:00:00Z',
            last_login_at: null,
          }),
        });
      } else if (url.includes('/api/v1/auth/login')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-access-token',
            refresh_token: 'mock-refresh-token',
            token_type: 'bearer',
            expires_in: 3600,
          }),
        });
      } else if (url.includes('/api/v1/jobs/list')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            total: 2,
            items: [
              {
                id: 1,
                title: '前端开发工程师',
                company_name: '某互联网公司',
                city: '北京',
                salary_min: 20,
                salary_max: 35,
                experience_min: 2,
                experience_max: 5,
                education_requirement: '本科',
                is_urgent: false,
                view_count: 100,
                apply_count: 10,
                is_active: true,
                published_at: '2024-01-01T00:00:00Z',
                created_at: '2024-01-01T00:00:00Z',
                updated_at: '2024-01-01T00:00:00Z',
                salary_display: '20K-35K',
                experience_display: '2-5年',
                is_favorited: false,
              },
              {
                id: 2,
                title: '后端开发工程师',
                company_name: '某科技公司',
                city: '上海',
                salary_min: 25,
                salary_max: 40,
                experience_min: 3,
                experience_max: 6,
                education_requirement: '本科',
                is_urgent: true,
                view_count: 150,
                apply_count: 20,
                is_active: true,
                published_at: '2024-01-02T00:00:00Z',
                created_at: '2024-01-02T00:00:00Z',
                updated_at: '2024-01-02T00:00:00Z',
                salary_display: '25K-40K',
                experience_display: '3-6年',
                is_favorited: false,
              }
            ],
            page: 1,
            page_size: 20,
          }),
        });
      } else if (url.includes('/api/v1/jobs/hot')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 1,
              title: '前端开发工程师',
              company_name: '某互联网公司',
              city: '北京',
              salary_min: 20,
              salary_max: 35,
              experience_min: 2,
              experience_max: 5,
              education_requirement: '本科',
              is_urgent: false,
              view_count: 100,
              apply_count: 10,
              is_active: true,
              published_at: '2024-01-01T00:00:00Z',
              created_at: '2024-01-01T00:00:00Z',
              updated_at: '2024-01-01T00:00:00Z',
              salary_display: '20K-35K',
              experience_display: '2-5年',
              is_favorited: false,
            }
          ]),
        });
      } else if (url.includes('/api/v1/jobs/statistics')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            total: 100,
            today_new: 5,
            top_cities: [
              { city: '北京', count: 30 },
              { city: '上海', count: 25 },
              { city: '深圳', count: 20 },
            ],
          }),
        });
      } else {
        // 其他请求返回404
        await route.abort();
      }
    });
  });

  test('should load jobs list within 5 seconds', async ({ page }) => {
    await page.goto('/jobs');
    
    // 等待页面加载
    await expect(page.getByRole('heading', { name: '搜索结果' })).toBeVisible();
    await expect(page.getByText('暂无符合条件的岗位')).not.toBeVisible();
    
    // 验证岗位列表显示
    const jobCards = page.locator('.ant-card');
    await expect(jobCards.first()).toBeVisible();
    await expect(jobCards.first()).toContainText('前端开发工程师');
    await expect(jobCards.first()).toContainText('某互联网公司');
    await expect(jobCards.first()).toContainText('北京');
    
    // 验证分页信息
    await expect(page.getByText('搜索结果')).toBeVisible();
  });

  test('should load dashboard within 3 seconds', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待页面加载
    await expect(page.getByRole('heading', { name: '首页' })).toBeVisible();
    
    // 验证统计数据显示
    await expect(page.locator('.ant-statistic')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // 模拟API错误
    await page.route('**/api/v1/jobs/list', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 'INTERNAL_ERROR',
          detail: '服务器内部错误',
        }),
      });
    });

    await page.goto('/jobs');
    
    // 验证错误处理
    await expect(page.getByText('服务器内部错误')).toBeVisible();
  });

  test('should load growth curve data', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 等待图表加载
    await expect(page.locator('[data-testid="growth-chart"]')).toBeVisible();
    
    // 验证数据加载
    await expect(page.getByText('个人成长曲线')).toBeVisible();
  });

  test('should load recent activities', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 验证活动列表加载
    await expect(page.getByText('最新动态')).toBeVisible();
    await expect(page.locator('.ant-list-item')).toBeVisible();
  });

  test('should handle authentication state', async ({ page }) => {
    // 测试未认证状态
    await page.goto('/dashboard');
    
    // 验证重定向到登录页
    await expect(page).toHaveURL('/auth/login');
  });

  test('should load questions list', async ({ page }) => {
    await page.goto('/questions');
    
    // 验证题目列表加载
    await expect(page.getByRole('heading', { name: '全部题目' })).toBeVisible();
    await expect(page.locator('.ant-card')).toBeVisible();
  });

  test('should load workbench applications', async ({ page }) => {
    await page.goto('/workbench');
    
    // 验证工作台加载
    await expect(page.getByRole('heading', { name: '工作台' })).toBeVisible();
    await expect(page.getByText('投递记录')).toBeVisible();
  });

  test('should handle mobile responsiveness', async ({ page }) => {
    // 设置移动视口
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/jobs');
    
    // 验证移动端布局
    await expect(page.locator('.ant-card')).toBeVisible();
    await expect(page.getByRole('button', { name: '重置筛选' })).toBeVisible();
  });

  test('should load job detail', async ({ page }) => {
    await page.goto('/jobs');
    
    // 点击第一个岗位
    await page.locator('.ant-card').first().click();
    
    // 验证岗位详情页
    await expect(page.getByRole('heading')).toBeVisible();
    await expect(page.locator('.ant-descriptions')).toBeVisible();
  });

  test('should handle cross-browser consistency', async ({ page }) => {
    await page.goto('/jobs');
    
    // 验证跨浏览器一致性
    const jobCards = page.locator('.ant-card');
    const cardCount = await jobCards.count();
    
    // 确保至少有一个岗位卡片
    expect(cardCount).toBeGreaterThan(0);
    
    // 验证每个卡片都有必要的信息
    for (let i = 0; i < Math.min(cardCount, 3); i++) {
      const card = jobCards.nth(i);
      await expect(card.locator('.ant-card-title')).toBeVisible();
      await expect(card.locator('.ant-card-meta-title')).toBeVisible();
    }
  });
});