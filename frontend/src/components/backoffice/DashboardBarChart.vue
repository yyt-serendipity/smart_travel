<template>
  <article class="card chart-card">
    <div class="title-row compact-row">
      <div>
        <strong>{{ title }}</strong>
        <p class="muted">{{ description }}</p>
      </div>
      <span class="pill">{{ items.length }} 项</span>
    </div>

    <div class="bar-chart">
      <div v-for="item in normalizedItems" :key="item.label" class="bar-chart-row">
        <div class="bar-chart-meta">
          <strong>{{ item.label }}</strong>
          <span class="muted">{{ item.value }}</span>
        </div>
        <div class="bar-chart-track">
          <div class="bar-chart-fill" :style="{ width: `${item.ratio}%` }"></div>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";


const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: "",
  },
  items: {
    type: Array,
    default: () => [],
  },
});

const normalizedItems = computed(() => {
  const max = Math.max(...props.items.map((item) => Number(item.value || 0)), 1);
  return props.items.map((item) => ({
    ...item,
    ratio: Math.max(8, (Number(item.value || 0) / max) * 100),
  }));
});
</script>
