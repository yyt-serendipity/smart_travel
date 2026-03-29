<template>
  <article class="card section-shell post-card post-card-upgraded">
    <div class="post-card-cover" :style="coverStyle">
      <div class="post-card-cover-overlay">
        <div class="post-topline">
          <div>
            <span class="eyebrow">Travel Post</span>
            <h3>{{ state.title }}</h3>
          </div>
          <span class="pill">{{ formatDate(state.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="post-card-body">
      <div class="post-card-body-head">
        <div class="community-author">
          <div class="community-avatar">
            <img v-if="state.author?.avatar_url" :src="state.author.avatar_url" :alt="state.author.nickname" />
            <span v-else>{{ state.author?.nickname?.slice(0, 1) || "游" }}</span>
          </div>
          <div>
            <strong>{{ state.author?.nickname || "旅行用户" }}</strong>
            <p class="muted">{{ state.city_name || "旅行社区" }}</p>
          </div>
        </div>

        <div class="post-info-strip">
          <span class="post-info-pill">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />
            </svg>
            <span>评论 {{ state.comment_count }}</span>
          </span>
          <span class="post-info-pill">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <span>浏览 {{ state.views_count }}</span>
          </span>
        </div>
      </div>

      <div class="post-card-subline">
        <span v-if="state.attraction_name" class="pill">{{ state.attraction_name }}</span>
      </div>

      <RichTextContent class="post-card-content" variant="compact" :html="state.content" :empty-text="state.content_preview" clamp />

      <div class="chip-row">
        <span v-for="tag in state.tags?.slice(0, 4)" :key="tag" class="pill">{{ tag }}</span>
      </div>

      <div class="post-action-strip">
        <div class="post-action-group">
          <button
            class="post-chip-button icon-chip-button"
            :class="{ active: state.liked, pending: state.likePending }"
            type="button"
            :disabled="!authState.user || state.likePending"
            aria-label="点赞帖子"
            @click="handleLike"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12.6 20.1 5.8 13.7a4.5 4.5 0 0 1 6.3-6.4L12 7.5l-.1-.2a4.5 4.5 0 0 1 6.3 6.4l-6.8 6.4a.6.6 0 0 1-.8 0Z" />
            </svg>
            <span>{{ state.likes_count }}</span>
          </button>
          <button
            class="post-chip-button icon-chip-button"
            :class="{ active: state.favorited, pending: state.favoritePending }"
            type="button"
            :disabled="!authState.user || state.favoritePending"
            aria-label="收藏帖子"
            @click="handleFavorite"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 4.5h12a1 1 0 0 1 1 1v14.2a.5.5 0 0 1-.8.4L12 15.3l-6.2 4.8a.5.5 0 0 1-.8-.4V5.5a1 1 0 0 1 1-1Z" />
            </svg>
            <span>{{ state.favorite_count }}</span>
          </button>
        </div>
        <div class="post-action-group">
          <RouterLink class="btn btn-secondary card-detail-button" :to="`/community/${state.id}`">查看帖子</RouterLink>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, reactive, watch, watchEffect } from "vue";
import { RouterLink } from "vue-router";

import RichTextContent from "./RichTextContent.vue";
import { authState } from "../stores/auth";
import {
  getPostEngagement,
  resolvePostEngagement,
  togglePostFavorite,
  togglePostLike,
} from "../stores/postEngagement";

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
});

const state = reactive({
  id: null,
  author: null,
  city_name: "",
  attraction_name: "",
  title: "",
  content: "",
  content_preview: "",
  cover_image: "",
  tags: [],
  likes_count: 0,
  favorite_count: 0,
  comment_count: 0,
  views_count: 0,
  liked: false,
  favorited: false,
  likePending: false,
  favoritePending: false,
  created_at: "",
});

function syncState(post) {
  const engagement = resolvePostEngagement(post);

  Object.assign(state, {
    id: post.id,
    author: post.author || null,
    city_name: post.city_name || post.city_detail?.name || "",
    attraction_name: post.attraction_name || post.attraction_detail?.name || "",
    title: post.title,
    content: post.content,
    content_preview: post.content_preview || "",
    cover_image: post.cover_image || "",
    tags: [...(post.tags || [])],
    likes_count: engagement.likes_count,
    favorite_count: engagement.favorite_count,
    comment_count: Number(post.comment_count || 0),
    views_count: Number(post.views_count || 0),
    liked: engagement.liked,
    favorited: engagement.favorited,
    likePending: engagement.likePending,
    favoritePending: engagement.favoritePending,
    created_at: post.created_at,
  });
}

watch(
  () => props.post,
  (post) => {
    if (!post) return;
    syncState(post);
  },
  { immediate: true, deep: true },
);

watchEffect(() => {
  const entry = getPostEngagement(state.id);
  if (!entry) return;

  state.liked = entry.liked;
  state.likes_count = entry.likes_count;
  state.favorited = entry.favorited;
  state.favorite_count = entry.favorite_count;
  state.likePending = entry.likePending;
  state.favoritePending = entry.favoritePending;
});

const coverStyle = computed(() => ({
  background: state.cover_image
    ? `linear-gradient(180deg, rgba(9, 34, 43, 0.1), rgba(9, 34, 43, 0.82)), url(${state.cover_image}) center/cover`
    : "linear-gradient(135deg, #103d4b, #0d5c63 55%, #f28f3b)",
}));

async function handleLike() {
  if (!authState.user || state.likePending) return;
  try {
    await togglePostLike(state.id);
  } catch (error) {
    console.error("Failed to toggle post like", error);
  }
}

async function handleFavorite() {
  if (!authState.user || state.favoritePending) return;
  try {
    await togglePostFavorite(state.id);
  } catch (error) {
    console.error("Failed to toggle post favorite", error);
  }
}

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString("zh-CN");
}
</script>

<style scoped>
.post-card-upgraded {
  overflow: hidden;
  padding: 0;
}

.post-card-cover {
  min-height: 180px;
}

.post-card-cover-overlay {
  min-height: 180px;
  display: grid;
  align-content: end;
  padding: 22px;
}

.post-card-cover-overlay :deep(.eyebrow) {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
}

.post-card-body {
  display: grid;
  gap: 18px;
  padding: 24px;
}

.post-topline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.post-topline h3 {
  margin: 12px 0 0;
  color: white;
}

.post-topline .pill {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
}

.post-card-body-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.post-card-subline {
  display: flex;
  justify-content: flex-end;
}

.post-info-strip {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.post-info-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  background: rgba(10, 94, 99, 0.08);
}

.post-info-pill svg {
  width: 14px;
  height: 14px;
}

.post-info-pill svg path,
.post-info-pill svg circle {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.post-action-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.post-card-content {
  min-height: 0;
}

.post-action-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.post-chip-button {
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid rgba(10, 94, 99, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: var(--secondary);
  cursor: pointer;
  transition: transform 0.18s ease, background 0.2s ease, color 0.2s ease, border-color 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease;
}

.post-chip-button:not(:disabled):hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.24);
  box-shadow: 0 10px 18px rgba(10, 68, 73, 0.1);
}

.icon-chip-button {
  gap: 8px;
}

.icon-chip-button svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.icon-chip-button svg path {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
  transition: transform 0.18s ease, fill 0.18s ease, stroke 0.18s ease;
  transform-origin: center;
}

.icon-chip-button:not(:disabled):hover svg path {
  transform: scale(1.12);
}

.post-chip-button.active {
  color: white;
  border-color: transparent;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 12px 22px rgba(10, 68, 73, 0.18);
}

.post-chip-button.active svg path {
  fill: currentColor;
  stroke: currentColor;
}

.post-chip-button.pending {
  opacity: 0.82;
}

@media (max-width: 720px) {
  .post-card-body,
  .post-card-cover-overlay {
    padding: 20px;
  }

  .post-card-body-head,
  .post-action-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .post-card-subline,
  .post-info-strip {
    justify-content: flex-start;
  }
}
</style>
