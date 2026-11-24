<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { REPOSITORY_URL } from '@/config'
</script>

<template>
  <footer class="site-footer">
    <div class="page columns small">
      <div>
        <p>
          <strong>Kindheit in Berlin</strong> ist ein Beitrag zum Berliner Open-Data-Ideenwettbewerb
          2026/2027.
        </p>
        <p>
          Alle Werte sind Modellrechnungen auf Grundlage offener Daten. Sie beschreiben Wege und
          Angebote, nicht die Qualität einer Kindheit.
        </p>
      </div>
      <div>
        <p>
          Daten: Land Berlin (dl-de/zero-2.0), Amt für Statistik Berlin-Brandenburg (CC BY 3.0 DE),
          Polizei Berlin (CC BY 4.0), Statistische Ämter des Bundes und der Länder (dl-de/by-2.0), ©
          <a href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende</a> (ODbL).
          <RouterLink to="/daten">Alle Quellen und Lizenzen</RouterLink>
        </p>
        <p>
          Texte und Grafiken:
          <a href="https://creativecommons.org/licenses/by/4.0/deed.de">CC BY 4.0</a>. Quellcode:
          MIT, <a :href="REPOSITORY_URL">GitHub</a>.
        </p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: var(--space-9);
  padding: var(--space-7) 0 var(--space-8);
  border-top: 1px solid var(--color-rule);
  color: var(--color-ink-secondary);
}
.columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
  gap: var(--space-5) var(--space-8);
}
</style>
