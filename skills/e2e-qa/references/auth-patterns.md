# E2E auth patterns

Three common patterns for getting tests past authentication. Pick by app type; the rest of the discipline lives in `SKILL.md`.

## 1. Cookie injection (test-endpoint apps)

Best for apps with a `/api/test/seed` endpoint (enabled via `TEST_MODE=1`). No browser login flow - per-test, fully isolated:

```ts
// helpers.ts
export async function seedAndAuth(request, context, email, tier = 'starter') {
  const { sessionTokens } = await seed(request, { users: [{ email, tier }] });
  await context.addCookies([{
    name: 'session', value: sessionTokens[email],
    domain: 'localhost', path: '/', httpOnly: true, sameSite: 'Strict',
  }]);
}

// in test
test('shows dashboard', async ({ page, request, context }) => {
  await seedAndAuth(request, context, 'e2e@example.com');
  await page.goto('/');
  await expect(page.getByRole('main')).toBeVisible();
});
```

## 2. storageState + globalSetup (OTP apps)

Best for OTP-login apps with `DEV_OTP_BYPASS=true`. Auth runs once in `globalSetup`, saved to `.auth/user.json`, reused across all tests:

```ts
// global-setup.ts - calls /api/auth/login + /api/auth/verify with code '000000'
// playwright.config.ts: globalSetup: './e2e/global-setup'

// in test
test.use({ storageState: 'e2e/.auth/user.json' });

test('shows dashboard', async ({ page }) => {
  // Mock /api/auth/me to avoid network round-trip
  await page.route('/api/auth/me', route =>
    route.fulfill({ status: 200, body: JSON.stringify({ user: { ... } }) })
  );
  await page.goto('/');
});
```

## 3. Full mocking (public apps / no auth)

For apps without auth or when testing specific API responses:

```ts
test.beforeEach(async ({ page }) => {
  await page.route('**/api/items*', route =>
    route.fulfill({ status: 200, body: JSON.stringify(fixtureScan) })
  );
});
```
