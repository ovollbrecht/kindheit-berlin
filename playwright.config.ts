import { defineConfig, devices } from '@playwright/test'

// The built site is copied into a sub-directory and served from there, exactly like a
// GitHub Pages project site (https://<user>.github.io/kindheit-berlin/).
const PORT = 4317
const SUB_PATH = '/kindheit-berlin/'

export default defineConfig({
  testDir: 'tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: { baseURL: `http://localhost:${PORT}${SUB_PATH}`, locale: 'de-DE' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: `rm -rf .e2e-site && mkdir -p .e2e-site${SUB_PATH} && cp -R dist/. .e2e-site${SUB_PATH} && npx vite preview --outDir .e2e-site --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}${SUB_PATH}`,
    reuseExistingServer: !process.env.CI,
  },
})
