<template>
  <article class="card chart-card donut-chart-card">
    <div class="title-row compact-row">
      <div>
        <strong>{{ title }}</strong>
        <p class="muted">{{ description }}</p>
      </div>
      <span class="pill">{{ total }}</span>
    </div>

    <div class="donut-chart-layout">
      <div class="donut-chart-ring" :style="{ background: chartBackground }">
        <div class="donut-chart-core">
          <strong>{{ total }}</strong>
          <span class="muted">总量</span>
        </div>
      </div>

      <div class="donut-chart-legend">
        <div v-for="item in normalizedItems" :key="item.label" class="donut-legend-item">
          <span class="donut-legend-dot" :style="{ background: item.color }"></span>
          <div>
            <strong>{{ item.label }}</strong>
            <p class="muted">{{ item.value }} · {{ item.percent }}%</p>
          </div>
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

const palette = ["#0d5c63", "#f28f3b", "#7bb2b8", "#1b4965", "#d95d39"];

const total = computed(() => props.items.reduce((sum, item) => sum + Number(item.value || 0), 0));
const normalizedItems = computed(() => {
  let cursor = 0;
  return props.items.map((item, index) => {
    const value = Number(item.value || 0);
    const percent = total.value ? Math.round((value / total.value) * 100) : 0;
    const start = cursor;
    cursor += percent;
    return {
      ...item,
      value,
      percent,
      start,
      end: cursor,
      color: item.color || palette[index % palette.length],
    };
  });
});

const chartBackground = computed(() => {
  if (!normalizedItems.value.length) {
    return "conic-gradient(#e7edef 0deg 360deg)";
  }
  let previous = 0;
  const stops = normalizedItems.value.map((item) => {
    const current = previous + item.percent;
    const stop = `${item.color} ${previous}% ${current}%`;
    previous = current;
    return stop;
  });
  return `conic-gradient(${stops.join(", ")})`;
});
</script>
