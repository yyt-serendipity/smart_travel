<template>
  <article class="card attraction-card attraction-card-upgraded">
    <div class="attraction-image" :style="imageStyle">
      <div class="attraction-image-overlay">
        <span class="pill attraction-city-pill">{{ attraction.city_name || cityName }}</span>
        <div v-if="attraction.rating" class="rating-burst">
          <small>评分</small>
          <strong>{{ attraction.rating }}</strong>
        </div>
      </div>
    </div>

    <div class="section-shell attraction-card-body">
      <div class="attraction-card-copy">
        <div class="attraction-card-summary">
          <h3>{{ attraction.name }}</h3>
          <ExpandableText v-if="expandable" :text="descriptionText" empty-text="暂无介绍" :min-length="52" />
          <p v-else class="muted">{{ descriptionText }}</p>
        </div>

        <div class="chip-row attraction-tag-row">
          <span v-if="attraction.suggested_play_time" class="tag-pill">{{ attraction.suggested_play_time }}</span>
          <span v-if="attraction.best_season" class="tag-pill">{{ attraction.best_season }}</span>
          <span v-for="tag in visibleTags" :key="tag" class="tag-pill">{{ tag }}</span>
        </div>
      </div>

      <RouterLink class="btn btn-secondary card-detail-button attraction-card-action" :to="`/attractions/${attraction.id}`">
        查看景点详情
      </RouterLink>
    </div>
  </article>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";

import ExpandableText from "./ExpandableText.vue";

const props = defineProps({
  attraction: {
    type: Object,
    required: true,
  },
  cityName: {
    type: String,
    default: "",
  },
  expandable: {
    type: Boolean,
    default: true,
  },
});

const descriptionText = computed(() => props.attraction.description || props.attraction.address || "暂无介绍");
const visibleTags = computed(() =>
  (props.attraction.tags || [])
    .map((tag) => String(tag || "").trim())
    .filter((tag, index, list) => tag && tag.length <= 10 && list.indexOf(tag) === index)
    .slice(0, 3),
);

const imageStyle = computed(() => ({
  background: props.attraction.image_url
    ? `linear-gradient(180deg, rgba(12, 57, 67, 0.08), rgba(12, 57, 67, 0.66)), url(${props.attraction.image_url}) center/cover`
    : "linear-gradient(135deg, #295d66, #7aa6ab 58%, #f2b166)",
}));
</script>

<style scoped>
.attraction-card-upgraded {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.attraction-image {
  min-height: 220px;
}

.attraction-image-overlay {
  min-height: 220px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
}

.attraction-city-pill {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
}

.rating-burst {
  min-width: 72px;
  display: grid;
  gap: 2px;
  justify-items: center;
  padding: 8px 12px;
  border-radius: 22px;
  color: white;
  background: linear-gradient(135deg, rgba(20, 61, 72, 0.84), rgba(13, 92, 99, 0.84));
  box-shadow: 0 12px 20px rgba(13, 92, 99, 0.18);
  backdrop-filter: blur(4px);
}

.rating-burst small,
.rating-burst strong {
  margin: 0;
  line-height: 1;
}

.rating-burst small {
  font-size: 10px;
  letter-spacing: 0.08em;
  opacity: 0.76;
}

.rating-burst strong {
  font-size: 24px;
  font-family: var(--heading-font);
}

.attraction-card-body {
  flex: 1 1 auto;
  min-height: 286px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.attraction-card-copy {
  flex: 1 1 auto;
  display: grid;
  gap: 16px;
  align-content: start;
}

.attraction-card-summary {
  min-height: 132px;
}

.attraction-card-summary h3,
.attraction-card-summary p {
  margin: 0;
}

.attraction-tag-row {
  gap: 10px;
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

.attraction-card-action {
  align-self: center;
  margin-top: auto;
  margin-bottom: 6px;
  min-width: 170px;
}
</style>
