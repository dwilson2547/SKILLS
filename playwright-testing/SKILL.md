---
name: playwright-testing
description: 'Write Playwright tests for a UI. Use when the user asks to add Playwright tests, write UI tests, or test a frontend. Also used as the verification standard within the ui-development skill.'
---

# Playwright Testing

Playwright tests must produce consistent, reliable results across runs. Flaky tests caused by
unstable selectors or arbitrary waits are worse than no tests — they create false confidence
and get disabled.

---

## Selector Priority

Always use the most stable selector available, in this order:

1. `getByRole('button', { name: 'Submit' })` — semantic, accessible, most stable
2. `getByLabel('Email address')` — form fields
3. `getByTestId('submit-btn')` — requires `data-testid` attribute in the markup
4. `getByText('Submit')` — exact visible text, use when role isn't specific enough
5. `locator('input[name="email"]')` — named attributes, acceptable
6. `locator('#submit-btn')` — stable IDs, acceptable
7. `locator('.submit-btn')` — CSS class, avoid unless class is semantically stable

**Never use generated class names** (e.g. `.css-1a2b3c`, Tailwind arbitrary values, hashed classes).

**If no stable selector exists for an element that needs testing — stop and ask the user**
before proceeding. Do not invent a workaround or skip the assertion.

---

## No Arbitrary Waits

Never use `page.waitForTimeout()`. Use explicit condition waits instead:

```typescript
// Wait for element
await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()

// Wait for navigation
await page.waitForURL('**/dashboard')

// Wait for network response
await page.waitForResponse(resp => resp.url().includes('/api/items') && resp.status() === 200)

// Wait for element to disappear
await expect(page.getByTestId('loading-spinner')).not.toBeVisible()
```

---

## Test Structure

One file per page or feature. Group related cases with `describe`.

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/route')
  })

  test('happy path', async ({ page }) => { ... })
  test('empty state', async ({ page }) => { ... })
  test('error state', async ({ page }) => { ... })
})
```

Every feature under test must cover:
- **Happy path** — the workflow completes successfully
- **Empty state** — correct UI when there is no data
- **Error state** — correct UI when a request fails or input is invalid

These are not optional. A feature is not tested if any of the three are missing.

---

## Triggering States

**Empty state:** ensure no seed data exists before the test, or navigate to a route
that has no associated records.

**Error state:** intercept the network request and force a failure:

```typescript
await page.route('**/api/items', route => route.fulfill({ status: 500 }))
```

**If you cannot determine how to reliably trigger a state — stop and ask the user.**
Do not mark a state as tested if you could not actually trigger it.

---

## Assertions

Prefer `expect` assertions that wait automatically over manual waits:

```typescript
// Visibility
await expect(locator).toBeVisible()
await expect(locator).not.toBeVisible()

// Content
await expect(locator).toHaveText('Expected text')
await expect(locator).toContainText('partial text')

// Count
await expect(page.getByRole('row')).toHaveCount(5)

// URL
await expect(page).toHaveURL('/expected-path')

// Attribute
await expect(locator).toHaveAttribute('aria-disabled', 'true')
```

---

## Test Isolation

Each test must be independent:
- Navigate fresh in `beforeEach` — do not rely on state from a previous test
- Do not share mutable state between tests
- If a test requires seeded data, seed it in `beforeEach` and clean up in `afterEach`

---

## Rules

- Stable selectors are non-negotiable — if one doesn't exist, add `data-testid` to the markup first
- Never use `waitForTimeout`
- Every tested feature must cover happy path, empty state, and error state
- Stop and ask the user when a selector is ambiguous or a state cannot be reliably triggered
- Do not skip or stub assertions to make tests pass — fix the underlying issue
