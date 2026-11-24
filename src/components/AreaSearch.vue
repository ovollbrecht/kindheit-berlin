<script setup lang="ts">
/** Search field for planning areas, built on the browser's own datalist. */
import { computed, ref, useId, watch } from 'vue'
import type { PlanningArea } from '@/domain/types'

const props = defineProps<{ areas: PlanningArea[]; label: string; selectedId?: string | null }>()
const emit = defineEmits<{ select: [id: string] }>()

const inputId = useId()
const listId = useId()
const displayName = (area: PlanningArea) => `${area.name} (${area.district})`
const byDisplayName = computed(
  () => new Map(props.areas.map((area) => [displayName(area), area.id])),
)
const sorted = computed(() => [...props.areas].sort((a, b) => a.name.localeCompare(b.name, 'de')))

const text = ref('')
watch(
  () => props.selectedId,
  (id) => {
    const area = props.areas.find((candidate) => candidate.id === id)
    text.value = area ? displayName(area) : ''
  },
  { immediate: true },
)

function onInput(): void {
  const id = byDisplayName.value.get(text.value)
  if (id && id !== props.selectedId) emit('select', id)
}
</script>

<template>
  <div class="field">
    <label :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      v-model="text"
      type="search"
      :list="listId"
      placeholder="Name eingeben …"
      autocomplete="off"
      @input="onInput"
      @change="onInput"
    />
    <datalist :id="listId">
      <option v-for="area in sorted" :key="area.id" :value="displayName(area)"></option>
    </datalist>
  </div>
</template>

<style scoped>
input {
  width: 100%;
}
</style>
