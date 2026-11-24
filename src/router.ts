import { createRouter, createWebHashHistory } from 'vue-router'

/** Page titles double as navigation labels. */
export const NAVIGATION = [
  { name: 'story', path: '/', label: 'Die Geschichte' },
  { name: 'explorer', path: '/explorer', label: 'Berlin-Explorer' },
  { name: 'compare', path: '/vergleich', label: 'Vergleich' },
  { name: 'potential', path: '/potenzial', label: 'Potenziale' },
  { name: 'methods', path: '/daten', label: 'Daten und Methodik' },
] as const

const SITE_TITLE = 'Kindheit in Berlin'

// Hash-based routing: GitHub Pages serves a single index.html and cannot rewrite paths.
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'story',
      component: () => import('./views/StoryView.vue'),
      meta: { title: 'Wege statt Kreise' },
    },
    {
      path: '/explorer',
      name: 'explorer',
      component: () => import('./views/ExplorerView.vue'),
      meta: { title: 'Berlin-Explorer' },
    },
    {
      path: '/quartier/:id',
      name: 'profile',
      component: () => import('./views/ProfileView.vue'),
      props: true,
      meta: { title: 'Quartiersprofil' },
    },
    {
      path: '/vergleich',
      name: 'compare',
      component: () => import('./views/CompareView.vue'),
      meta: { title: 'Quartiersvergleich' },
    },
    {
      path: '/potenzial',
      name: 'potential',
      component: () => import('./views/PotentialView.vue'),
      meta: { title: 'Potenziale' },
    },
    {
      path: '/daten',
      name: 'methods',
      component: () => import('./views/MethodsView.vue'),
      meta: { title: 'Daten und Methodik' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('./views/NotFoundView.vue'),
      meta: { title: 'Seite nicht gefunden' },
    },
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    // Changing only query parameters (filters) must not jump to the top.
    if (to.path === from.path) return false
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '')} – ${SITE_TITLE}`
})
