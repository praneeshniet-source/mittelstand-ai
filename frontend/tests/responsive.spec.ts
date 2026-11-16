
import { test, expect } from '@playwright/test'

const viewports = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
]

for (const viewport of viewports) {
  test(`Dashboard renders correctly at ${viewport.name} size`, async ({ page }) => {
    const browserErrors: string[] = []

    page.on('pageerror', (error) => {
      browserErrors.push(error.message)
    })

    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    })

    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle',
    })

    await expect(
      page.getByRole('heading', { name: 'Dashboard' }),
    ).toBeVisible()

    await expect(
      page.getByText('Invoice Explorer'),
    ).toBeVisible()

    await expect(
      page.getByText('Payment risk overview'),
    ).toBeVisible()

    await expect(
      page.getByRole('heading', { name: 'POKO', exact: true }),
    ).toBeVisible()

    const layout = await page.evaluate(() => ({
      viewportWidth: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
    }))

    expect(
      layout.documentWidth,
      `Horizontal overflow at ${viewport.name}: ${JSON.stringify(layout)}`,
    ).toBeLessThanOrEqual(viewport.width)

    expect(browserErrors).toEqual([])
  })
}
