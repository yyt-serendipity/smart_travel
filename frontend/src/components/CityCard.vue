<template>
  <article class="card city-card city-card-upgraded">
    <div class="city-cover" :style="coverStyle">
      <span class="pill city-province-pill">{{ city.province || "中国" }}</span>
      <div v-if="city.average_rating" class="city-rating-badge">
        <span class="city-rating-star">★</span>
        <strong>{{ city.average_rating }}</strong>
      </div>
    </div>
    <div class="section-shell city-card-body">
      <div class="title-row">
        <div class="city-card-copy">
          <h3>{{ city.name }}</h3>
          <ExpandableText :text="summaryText" empty-text="暂无城市概览" :min-length="48" />
        </div>
      </div>
      <div class="chip-row">
        <span class="pill">{{ city.recommended_days }} 天</span>
        <span class="pill">{{ city.attraction_count }} 景点</span>
        <span v-for="tag in city.tags?.slice(0, 3)" :key="tag" class="tag-pill">{{ tag }}</span>
      </div>
      <RouterLink class="btn btn-secondary card-detail-button city-card-action" :to="`/cities/${city.id}`">查看详情</RouterLink>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";

import ExpandableText from "./ExpandableText.vue";


const props = defineProps({
  city: {
    type: Object,
    required: true,
  },
});

const summaryText = computed(() => props.city.short_intro || props.city.overview || "暂无城市概览");

const coverStyle = computed(() => ({
  background: props.city.cover_image
    ? `linear-gradient(180deg, rgba(12, 57, 67, 0.14), rgba(12, 57, 67, 0.76)), url(${props.city.cover_image}) center/cover`
    : "linear-gradient(135deg, #0d5c63, #2a9d8f 55%, #f4a261)",
}));
</script>

<style scoped>
.city-card-upgraded {
  overflow: hidden;
}

.city-cover {
  min-height: 190px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 18px;
}

.city-province-pill {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.12);
}

.city-rating-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  color: white;
  background: linear-gradient(135deg, #f2a43d, #ff7447);
  box-shadow: 0 16px 26px rgba(255, 116, 71, 0.24);
}

.city-rating-star {
  font-size: 18px;
  line-height: 1;
}

.city-rating-badge strong {
  font-size: 24px;
  line-height: 1;
  font-family: var(--heading-font);
}

.city-card-body {
  display: grid;
  gap: 18px;
  min-height: 254px;
}

.city-card-copy {
  display: grid;
  gap: 10px;
}

.city-card-copy h3,
.city-card-copy p {
  margin: 0;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  color: var(--secondary);
  font-size: 12px;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(242, 143, 59, 0.18), rgba(10, 94, 99, 0.1));
  border: 1px solid rgba(10, 94, 99, 0.08);
}

.city-card-action {
  justify-self: center;
  margin-top: auto;
}

@media (max-width: 720px) {
  .city-cover {
    min-height: 168px;
    padding: 16px;
  }

  .city-card-body {
    min-height: auto;
    gap: 16px;
  }

  .city-card-action {
    width: 100%;
    justify-self: stretch;
  }
}
</style>
