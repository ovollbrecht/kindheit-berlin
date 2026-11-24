<script setup lang="ts">
/**
 * Map of the planning areas, coloured by class. MapLibre is loaded on demand and draws
 * only our own GeoJSON: no base map, no external tiles, no third-party requests.
 * The map is a visual aid; every view offers the same information as a table or list.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type {
  ExpressionSpecification,
  GeoJSONSource,
  Map as MapLibreMap,
  Marker,
  Popup,
} from 'maplibre-gl'
import { NO_DATA_COLOR } from '@/domain/colors'
import type { AreaGeometries, DistrictGeometries } from '@/services/data'

export interface MapPoint {
  id: string
  lon: number
  lat: number
  /** Short text inside the marker, e.g. the rank. */
  badge: string
  /** Full description for the tooltip and for screen readers. */
  title: string
}

const props = defineProps<{
  areas: AreaGeometries
  districts: DistrictGeometries
  /** Fill colour per planning-area id; areas without an entry are drawn as "no data". */
  colors: Map<string, string>
  /** Text shown when hovering an area, per planning-area id. */
  tooltips: Map<string, string>
  selectedId?: string | null
  points?: MapPoint[]
  label: string
}>()
const emit = defineEmits<{ select: [id: string] }>()

const BERLIN_BOUNDS: [[number, number], [number, number]] = [
  [13.08, 52.33],
  [13.77, 52.68],
]
const MAX_BOUNDS: [[number, number], [number, number]] = [
  [12.6, 52.1],
  [14.2, 52.9],
]
const PAPER = '#faf8f3'
const AREA_BORDER = '#faf8f3'
const DISTRICT_BORDER = '#1a1c1e'
const ATTRIBUTION = 'Geometrie: Amt für Statistik Berlin-Brandenburg, LOR 2021 (CC BY 3.0 DE)'
/** German texts for MapLibre's own controls and hints. */
const MAP_LOCALE = {
  'CooperativeGesturesHandler.WindowsHelpText':
    'Strg gedrückt halten und scrollen, um die Karte zu zoomen',
  'CooperativeGesturesHandler.MacHelpText':
    '⌘ gedrückt halten und scrollen, um die Karte zu zoomen',
  'CooperativeGesturesHandler.MobileHelpText': 'Karte mit zwei Fingern bewegen',
  'NavigationControl.ZoomIn': 'Vergrößern',
  'NavigationControl.ZoomOut': 'Verkleinern',
  'AttributionControl.ToggleAttribution': 'Quellenangabe ein- oder ausblenden',
  'Map.Title': 'Karte',
}

const container = ref<HTMLElement | null>(null)
const failed = ref(false)
let map: MapLibreMap | null = null
let popup: Popup | null = null
let pointMarkers: Marker[] = []
let createMarker: ((element: HTMLElement, lon: number, lat: number) => Marker) | null = null

function fillExpression(): ExpressionSpecification | string {
  if (props.colors.size === 0) return NO_DATA_COLOR
  const pairs = [...props.colors.entries()].flat()
  return ['match', ['get', 'id'], ...pairs, NO_DATA_COLOR] as unknown as ExpressionSpecification
}

function updateColors(): void {
  if (map?.getLayer('areas-fill'))
    map.setPaintProperty('areas-fill', 'fill-color', fillExpression())
}

function updateSelection(): void {
  if (map?.getLayer('areas-selected'))
    map.setFilter('areas-selected', ['==', ['get', 'id'], props.selectedId ?? ''])
}

function updatePoints(): void {
  pointMarkers.forEach((marker) => marker.remove())
  pointMarkers = []
  if (!map || !createMarker) return
  for (const point of props.points ?? []) {
    const element = document.createElement('div')
    element.className = 'map-point'
    element.textContent = point.badge
    element.title = point.title
    pointMarkers.push(createMarker(element, point.lon, point.lat))
  }
}

onMounted(async () => {
  if (!container.value) return
  try {
    const maplibre = await import('maplibre-gl')
    await import('maplibre-gl/dist/maplibre-gl.css')
    // MapLibre locates its worker relative to its own file, which bundlers relocate:
    // hand it the bundled worker explicitly.
    const worker = await import('maplibre-gl/dist/maplibre-gl-worker.mjs?url')
    maplibre.setWorkerUrl(worker.default)
    const instance = new maplibre.Map({
      container: container.value,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: 'background', type: 'background', paint: { 'background-color': PAPER } }],
      },
      bounds: BERLIN_BOUNDS,
      fitBoundsOptions: { padding: 12 },
      maxBounds: MAX_BOUNDS,
      minZoom: 8,
      maxZoom: 15,
      dragRotate: false,
      pitchWithRotate: false,
      touchPitch: false,
      // Scrolling the page must not be captured by the map.
      cooperativeGestures: true,
      locale: MAP_LOCALE,
      attributionControl: { customAttribution: ATTRIBUTION, compact: true },
    })
    map = instance
    instance.touchZoomRotate.disableRotation()
    instance.addControl(new maplibre.NavigationControl({ showCompass: false }), 'top-right')
    popup = new maplibre.Popup({ closeButton: false, closeOnClick: false, offset: 10 })
    createMarker = (element, lon, lat) =>
      new maplibre.Marker({ element }).setLngLat([lon, lat]).addTo(instance)

    instance.on('load', () => {
      instance.addSource('areas', { type: 'geojson', data: props.areas })
      instance.addSource('districts', { type: 'geojson', data: props.districts })
      instance.addLayer({
        id: 'areas-fill',
        type: 'fill',
        source: 'areas',
        paint: { 'fill-color': fillExpression() },
      })
      instance.addLayer({
        id: 'areas-border',
        type: 'line',
        source: 'areas',
        paint: { 'line-color': AREA_BORDER, 'line-width': 0.6 },
      })
      instance.addLayer({
        id: 'districts-border',
        type: 'line',
        source: 'districts',
        paint: { 'line-color': DISTRICT_BORDER, 'line-width': 1.1, 'line-opacity': 0.55 },
      })
      instance.addLayer({
        id: 'areas-selected',
        type: 'line',
        source: 'areas',
        paint: { 'line-color': '#b8431a', 'line-width': 3 },
        filter: ['==', ['get', 'id'], props.selectedId ?? ''],
      })
      for (const district of props.districts.features) {
        const element = document.createElement('div')
        element.className = 'map-district-label'
        element.textContent = district.properties.name
        new maplibre.Marker({ element })
          .setLngLat([district.properties.labelLon, district.properties.labelLat])
          .addTo(instance)
      }
      updatePoints()
    })

    instance.on('mousemove', 'areas-fill', (event) => {
      const id = event.features?.[0]?.properties.id as string | undefined
      const text = id ? props.tooltips.get(id) : undefined
      instance.getCanvas().style.cursor = 'pointer'
      if (text) popup?.setLngLat(event.lngLat).setText(text).addTo(instance)
    })
    instance.on('mouseleave', 'areas-fill', () => {
      instance.getCanvas().style.cursor = ''
      popup?.remove()
    })
    instance.on('click', 'areas-fill', (event) => {
      const id = event.features?.[0]?.properties.id as string | undefined
      if (id) emit('select', id)
    })
  } catch {
    // For example when WebGL is unavailable; the tables remain fully usable.
    failed.value = true
  }
})

watch(() => props.colors, updateColors)
watch(() => props.selectedId, updateSelection)
watch(() => props.points, updatePoints)
watch(
  () => props.areas,
  (areas) => (map?.getSource('areas') as GeoJSONSource | undefined)?.setData(areas),
)

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <div class="map-frame">
    <div ref="container" class="map" role="application" :aria-label="label"></div>
    <p v-if="failed" class="fallback note">
      Die Karte kann in diesem Browser nicht dargestellt werden. Alle Werte stehen in der Tabelle.
    </p>
  </div>
</template>

<style scoped>
.map-frame {
  position: relative;
}
.map {
  width: 100%;
  aspect-ratio: 5 / 4;
  max-height: 38rem;
  min-height: 18rem;
  border: 1px solid var(--color-rule);
  background: var(--color-paper);
}
.fallback {
  position: absolute;
  inset: var(--space-5);
  height: fit-content;
}
</style>

<style>
/* Elements created by MapLibre live outside Vue's scoped styles. */
.map-district-label {
  pointer-events: none;
  font-family: var(--font-text);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--color-ink);
  text-shadow:
    0 0 3px #fff,
    0 0 3px #fff,
    0 0 2px #fff;
  white-space: nowrap;
}
.map-point {
  display: grid;
  place-items: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  border: 2px solid #fff;
  background: var(--color-highlight);
  color: #fff;
  font-family: var(--font-text);
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 1px 3px rgb(0 0 0 / 35%);
}
.maplibregl-popup-content {
  font-family: var(--font-text);
  font-size: var(--size-small);
  padding: var(--space-2) var(--space-3);
  white-space: pre-line;
}
</style>
