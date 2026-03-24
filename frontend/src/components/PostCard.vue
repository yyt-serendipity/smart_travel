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
      <div class="title-row compact-row">
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
        <div class="chip-row">
          <span v-if="state.attraction_name" class="pill">{{ state.attraction_name }}</span>
        </div>
      </div>

      <p class="muted clamp-4">{{ state.content }}</p>

      <div class="chip-row">
        <span v-for="tag in state.tags?.slice(0, 4)" :key="tag" class="pill">{{ tag }}</span>
      </div>

      <div class="post-action-strip">
        <div class="post-action-group">
          <button class="post-chip-button" :class="{ active: state.liked }" type="button" :disabled="!authState.user" @click="handleLike">
            点赞 {{ state.likes_count }}
          </button>
          <button
            class="post-chip-button"
            :class="{ active: state.favorited }"
            type="button"
            :disabled="!authState.user"
            @click="handleFavorite"
          >
            收藏 {{ state.favorite_count }}
          </button>
        </div>
        <div class="post-action-group">
          <span class="muted">评论 {{ state.comment_count }}</span>
          <span class="muted">浏览 {{ state.views_count }}</span>
          <RouterLink class="btn btn-secondary card-detail-button" :to="`/community/${state.id}`">查看帖子</RouterLink>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { RouterLink } from "vue-router";

import { toggleFavorite, toggleLike } from "../services/api";
import { authState } from "../stores/auth";


const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
});

const state = reactive({});

function syncState(post) {
  Object.assign(state, {
    id: post.id,
    author: post.author || null,
    city_name: post.city_name || post.city_detail?.name || "",
    attraction_name: post.attraction_name || post.attraction_detail?.name || "",
    title: post.title,
    content: post.content,
    cover_image: post.cover_image || "",
    tags: [...(post.tags || [])],
    likes_count: Number(post.likes_count || 0),
    favorite_count: Number(post.favorite_count || 0),
    comment_count: Number(post.comment_count || 0),
    views_count: Number(post.views_count || 0),
    liked: Boolean(post.liked),
    favorited: Boolean(post.favorited),
    created_at: post.created_at,
  });
}

watch(
  () => props.post,
  (post) => syncState(post),
  { immediate: true, deep: true },
);

const coverStyle = computed(() => ({
  background: state.cover_image
    ? `linear-gradient(180deg, rgba(9, 34, 43, 0.1), rgba(9, 34, 43, 0.82)), url(${state.cover_image}) center/cover`
    : "linear-gradient(135deg, #103d4b, #0d5c63 55%, #f28f3b)",
}));

async function handleLike() {
  if (!authState.user) return;
  const data = await toggleLike(state.id);
  state.liked = data.liked;
  state.likes_count = data.likes_count;
}

async function handleFavorite() {
  if (!authState.user) return;
  const data = await toggleFavorite(state.id);
  state.favorited = data.favorited;
  state.favorite_count = data.favorite_count;
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

.post-action-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
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
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.post-chip-button.active {
  color: white;
  border-color: transparent;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
}
</style>
