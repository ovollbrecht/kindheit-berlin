import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const PAGES = [
  { name: 'story', path: './', ready: 'Der Kreis auf der Karte täuscht' },
  { name: 'explorer', path: './#/explorer?area=11401137', ready: 'Alle Planungsräume' },
  { name: 'profile', path: './#/quartier/11401137', ready: 'Was ist in der Nähe?' },
  {
    name: 'comparison',
    path: './#/vergleich?a=05200631&b=11401137',
    ready: 'Wege und Angebote im Vergleich',
  },
  { name: 'potential', path: './#/potenzial', ready: 'Annahmen der Rechnung' },
  { name: 'methods', path: './#/daten', ready: 'Quellen und Lizenzen' },
]

for (const { name, path, ready } of PAGES) {
  test(`${name} has no automatically detectable WCAG 2.2 AA violations`, async ({ page }) => {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: ready })).toBeVisible()
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      // The map canvas is drawn by MapLibre; its content is offered as a table next to it.
      .exclude('.maplibregl-canvas-container')
      .analyze()
    expect(
      results.violations.map(
        (violation) => `${violation.id}: ${violation.nodes.map((node) => node.target).join(' | ')}`,
      ),
    ).toEqual([])
  })
}

test('no page scrolls sideways on a phone', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile')
  for (const { path, ready } of PAGES) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: ready })).toBeVisible()
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, path).toBeLessThanOrEqual(1)
  }
})
