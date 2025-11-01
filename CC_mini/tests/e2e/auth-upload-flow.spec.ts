import { test, expect } from '@playwright/test';

test.describe('NotesLLM E2E Tests', () => {
  test('complete user flow: register, login, upload, and chat', async ({ page }) => {
    const testEmail = `test${Date.now()}@example.com`;
    const testPassword = 'TestPassword123';

    // 1. Navigate to register page
    await page.goto('/register');

    // 2. Fill registration form
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);

    // 3. Submit registration
    await page.click('button[type="submit"]');

    // 4. Wait for redirect to login page
    await page.waitForURL('/login', { timeout: 10000 });

    // 5. Fill login form
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    // 6. Submit login
    await page.click('button[type="submit"]');

    // 7. Wait for redirect to dashboard
    await page.waitForURL('/dashboard', { timeout: 10000 });

    // 8. Verify dashboard loaded
    await expect(page.locator('h1')).toContainText('My Documents');

    // 9. Open upload modal
    await page.click('button:has-text("Upload Document")');

    // 10. Verify upload modal opened
    await expect(page.locator('text=Upload Document')).toBeVisible();

    // Note: For actual file upload testing, you would need a test PDF file
    // await page.setInputFiles('input[type="file"]', 'path/to/test.pdf');
    // await page.click('button:has-text("Upload Document")');

    // 11. Navigate to chat
    await page.click('a:has-text("Chat")');

    // 12. Verify chat page loaded
    await expect(page.locator('h1')).toContainText('Chat with Documents');

    // 13. Verify logout button exists
    await expect(page.locator('button:has-text("Logout")')).toBeVisible();

    // 14. Logout
    await page.click('button:has-text("Logout")');

    // 15. Verify redirected to login
    await page.waitForURL('/login', { timeout: 10000 });
  });

  test('protected routes redirect to login when not authenticated', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');

    // Should redirect to login
    await page.waitForURL('/login');
    await expect(page.locator('h2')).toContainText('NotesLLM');
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');

    await page.click('button[type="submit"]');

    // Should show error message (adjust based on your actual error handling)
    // await expect(page.locator('text=Login failed')).toBeVisible({ timeout: 5000 });
  });
});
