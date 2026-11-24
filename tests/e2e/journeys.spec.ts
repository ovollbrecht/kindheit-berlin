import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  // Any uncaught error or failed request fails the test.
  page.on('pageerror', (error) => {
    throw error
  })
  page.on('response', (response) => {
    if (response.status() >= 400) throw new Error(`${response.status()} ${response.url()}`)
  })
})

test('the story shows the headline figures and leads into the explorer', async ({ page }) => {
  await page.goto('./')
  await expect(page.getByRole('heading', { level: 1, name: 'Wege statt Kreise' })).toBeVisible()
  await expect(page.getByText('86 %').first()).toBeVisible()
  await expect(page.getByText('70 %').first()).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Der Kreis auf der Karte täuscht' })).toBeVisible()

  await page.getByRole('link', { name: /Im Explorer nachsehen/ }).click()
  await expect(page).toHaveURL(/#\/explorer\?ind=playgroundReach/)
  await expect(page.getByRole('heading', { level: 1 })).toContainText(
    'Wie sieht es im eigenen Quartier aus?',
  )
})

test('every chart offers its data as a table', async ({ page }) => {
  await page.goto('./')
  const tables = page.getByText('Daten als Tabelle')
  await expect(tables).toHaveCount(6)
  await tables.first().click()
  await expect(page.getByRole('cell', { name: '86 %' }).first()).toBeVisible()
})

test('the explorer finds an area, keeps the view in the URL and opens the profile', async ({
  page,
}) => {
  await page.goto('./#/explorer')
  await page.getByLabel('Kennzahl').selectOption('playM2PerChild')
  await expect(page).toHaveURL(/ind=playM2PerChild/)
  await expect(page.getByLabel('Entfernung')).toHaveCount(0)

  await page.getByLabel('Planungsraum suchen').fill('Erieseering (Lichtenberg)')
  await expect(page).toHaveURL(/area=11401137/)
  const selection = page.getByRole('complementary')
  await expect(selection.getByRole('heading', { name: 'Erieseering' })).toBeVisible()
  await expect(selection).toContainText('7,5 m²')

  // A shared link restores the same view.
  await page.reload()
  await expect(page.getByLabel('Kennzahl')).toHaveValue('playM2PerChild')
  await expect(selection.getByRole('heading', { name: 'Erieseering' })).toBeVisible()

  await selection.getByRole('link', { name: 'Quartiersprofil öffnen' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Erieseering' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Was ist in der Nähe?' })).toBeVisible()
})

test('the distance and the way of measuring change the explorer values', async ({ page }) => {
  await page.goto('./#/explorer?area=12601235')
  const selection = page.getByRole('complementary')
  await expect(selection).toContainText('0 %')
  await page.getByLabel('Gemessen als').selectOption('withOsm')
  await expect(selection).toContainText('100 %')
  await page.getByLabel('Entfernung').selectOption('1000')
  await expect(page).toHaveURL(/dist=1000/)
})

test('the table can be sorted with the keyboard', async ({ page }) => {
  await page.goto('./#/explorer')
  const header = page.getByRole('columnheader', { name: /Kinder unter 18/ })
  await header.getByRole('button').focus()
  await page.keyboard.press('Enter')
  await expect(header).toHaveAttribute('aria-sort', 'ascending')
  await page.keyboard.press('Enter')
  await expect(header).toHaveAttribute('aria-sort', 'descending')
})

test('the comparison suggests similar areas and shows both side by side', async ({ page }) => {
  await page.goto('./#/vergleich')
  await page.getByRole('link', { name: /Wilhelmstadt Ost .* Erieseering/ }).click()
  await expect(page.getByRole('heading', { name: 'Wie ähnlich sind die beiden?' })).toBeVisible()
  await expect(page.getByRole('columnheader', { name: 'Wilhelmstadt Ost' }).first()).toBeVisible()
  await expect(
    page.getByRole('heading', { name: /Ähnliche Quartiere zu Wilhelmstadt Ost/ }),
  ).toBeVisible()

  // Choosing another suggestion replaces the second area.
  await page.locator('.suggestion[aria-pressed="false"]').first().click()
  await expect(page).not.toHaveURL(/b=11401137/)
  await expect(page.locator('.suggestion[aria-pressed="true"]')).toHaveCount(1)
})

test('the potential explorer recalculates when the number of sites changes', async ({ page }) => {
  await page.goto('./#/potenzial')
  await expect(page.getByRole('heading', { name: 'Die 10 wirksamsten Standorte' })).toBeVisible()
  await expect(page.getByText('Das ist keine Planungsempfehlung.')).toBeVisible()
  await page.getByLabel(/Anzahl der Standorte/).fill('3')
  await expect(page.getByRole('heading', { name: 'Die 3 wirksamsten Standorte' })).toBeVisible()
  await expect(page.locator('tbody tr')).toHaveCount(3)
  await page.getByLabel(/vorsichtig/).check()
  await expect(page).toHaveURL(/basis=withOsm/)
})

test('the methodology page lists sources with licences and offers downloads', async ({ page }) => {
  await page.goto('./#/daten')
  await expect(page.getByRole('link', { name: 'Einwohnerdichte 2025 (Umweltatlas)' })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'ODbL 1.0' })).toBeVisible()
  const download = page.getByRole('link', { name: /Alle Kennzahlen je Planungsraum/ })
  const response = await page.request.get((await download.getAttribute('href')) ?? '')
  expect(response.ok()).toBe(true)
})

test('an unknown address explains itself instead of showing an empty page', async ({ page }) => {
  await page.goto('./#/gibt-es-nicht')
  await expect(page.getByRole('heading', { name: 'Diese Seite gibt es nicht' })).toBeVisible()
  await page.goto('./#/quartier/00000000')
  await expect(page.getByRole('heading', { name: 'Quartier nicht gefunden' })).toBeVisible()
})

test('keyboard users can skip the navigation', async ({ page }) => {
  await page.goto('./')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Zum Inhalt springen' })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('main')).toBeFocused()
})
