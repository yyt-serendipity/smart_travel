<template>
  <article class="card community-feed-post community-feed-post-upgraded">
    <div class="community-feed-post-cover" :style="coverStyle">
      <div class="community-feed-post-cover-overlay">
        <div class="community-feed-post-topline">
          <div>
            <span class="community-feed-post-note">旅行帖子</span>
            <h3>{{ state.title }}</h3>
          </div>
          <span class="pill community-feed-post-date">{{ formatDate(state.created_at) }}</span>
        </div>
        <p class="community-feed-post-meta">
          {{ state.city_name || "旅行社区" }}
          <template v-if="state.attraction_name"> · {{ state.attraction_name }}</template>
        </p>
      </div>
    </div>

    <div class="community-feed-post-body">
      <div class="title-row compact-row">
        <div class="community-author">
          <div class="community-avatar">
            <img v-if="state.author?.avatar_url" :src="state.author.avatar_url" :alt="state.author.nickname" />
            <span v-else>{{ state.author?.nickname?.slice(0, 1) || "游" }}</span>
          </div>
          <div>
            <strong>{{ state.author?.nickname || "旅行用户" }}</strong>
            <p class="muted">{{ state.city_name || "中国旅行社区" }}</p>
          </div>
        </div>
        <div class="chip-row">
          <span v-if="state.attraction_name" class="pill">{{ state.attraction_name }}</span>
        </div>
      </div>

      <p class="muted clamp-4">{{ state.content }}</p>

      <div class="chip-row">
        <span v-for="tag in state.tags?.slice(0, 4)" :key="tag" class="tag-pill">{{ tag }}</span>
      </div>

      <div class="community-feed-post-actions community-post-action-strip">
        <div class="post-action-group">
          <button class="post-chip-button" :class="{ active: state.liked }" type="button" :disabled="!authState.user" @click="handleLike">
            点赞 {{ state.likes_count }}
          </button>
          <button class="post-chip-button" :class="{ active: state.favorited }" type="button" :disabled="!authState.user" @click="handleFavorite">
            收藏 {{ state.favorite_count }}
          </button>
        </div>
        <div class="post-action-group">
          <span class="muted">评论 {{ state.comment_count }}</span>
          <span class="muted">浏览 {{ state.views_count }}</span>
          <RouterLink class="btn btn-secondary card-detail-button" :to="`/community/${state.id}`">查看全文</RouterLink>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, reactive, watch } from "vue";
import { RouterLink } from "vue-router";

import { toggleFavorite, toggleLike } from "../../services/api";
import { authState } from "../../stores/auth";

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
.community-feed-post-upgraded {
  overflow: hidden;
  padding: 0;
}

.community-feed-post-cover {
  min-height: 190px;
}

.community-feed-post-cover-overlay {
  min-height: 190px;
  display: grid;
  align-content: end;
  gap: 10px;
  padding: 22px;
}

.community-feed-post-topline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.community-feed-post-note {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.14);
}

.community-feed-post-topline h3 {
  margin: 12px 0 0;
  color: white;
}

.community-feed-post-date {
  align-self: flex-start;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.12);
}

.community-feed-post-meta {
  margin: 0;
  color: rgba(255, 255, 255, 0.84);
  font-size: 14px;
}

.community-feed-post-body {
  display: grid;
  gap: 18px;
  padding: 24px;
}

.community-feed-post-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.community-post-action-strip {
  padding-top: 4px;
}
</style>
