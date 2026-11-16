<script setup>
import SummaryCard from './SummaryCard.vue'

defineProps({
  cards: { type: Array, required: true },
  cols: { type: Number, default: 4 },
})
</script>

<template>
  <div class="mb-4 gap-3" :style="{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)` }">
    <SummaryCard
      v-for="(card, i) in cards"
      :key="i"
      :label="card.label"
      :value="card.value"
      :tag="card.tag"
      :tagColor="card.tagColor"
    />
  </div>
</template>
