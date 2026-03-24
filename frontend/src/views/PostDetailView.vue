<template>
  <section class="page">
    <div class="page-toolbar">
      <PageBackButton :fallback-to="{ name: 'community' }" label="返回社区" />
      <div class="action-row">
        <RouterLink v-if="post?.city_detail" class="btn btn-secondary" :to="{ name: 'community', query: { cityId: post.city_detail.id } }">
          查看同城帖子
        </RouterLink>
        <RouterLink
          v-if="post?.attraction_detail"
          class="btn btn-secondary"
          :to="{ name: 'attraction-detail', params: { id: post.attraction_detail.id } }"
        >
          查看关联景点
        </RouterLink>
      </div>
    </div>

    <template v-if="post">
      <div class="post-detail-layout">
        <article class="card post-detail-card">
          <div class="post-detail-cover post-detail-cover-shell" :style="postCoverStyle">
            <div class="post-detail-cover-overlay">
              <span class="eyebrow">Travel Feed</span>
              <h1 class="hero-title">{{ post.title }}</h1>
              <p class="hero-subtitle">{{ post.city_detail?.name || "中国旅行社区" }} · {{ formatDate(post.created_at) }}</p>
            </div>
          </div>

          <div class="section-shell post-detail-body">
            <div class="post-detail-head">
              <div class="community-author">
                <div class="community-avatar">
                  <img v-if="post.author.avatar_url" :src="post.author.avatar_url" :alt="post.author.nickname" />
                  <span v-else>{{ post.author.nickname?.slice(0, 1) || "游" }}</span>
                </div>
                <div>
                  <strong>{{ post.author.nickname }}</strong>
                  <p class="muted">发布于 {{ formatDate(post.created_at) }}</p>
                </div>
              </div>

              <div class="post-stat-grid post-stat-grid-4">
                <div class="mini-spot">
                  <strong>{{ post.likes_count }}</strong>
                  <p class="muted">点赞</p>
                </div>
                <div class="mini-spot">
                  <strong>{{ post.favorite_count }}</strong>
                  <p class="muted">收藏</p>
                </div>
                <div class="mini-spot">
                  <strong>{{ totalComments }}</strong>
                  <p class="muted">评论</p>
                </div>
                <div class="mini-spot">
                  <strong>{{ post.views_count }}</strong>
                  <p class="muted">浏览</p>
                </div>
              </div>
            </div>

            <div class="chip-row">
              <span v-for="tag in post.tags || []" :key="tag" class="pill">{{ tag }}</span>
              <RouterLink
                v-if="post.attraction_detail"
                class="pill"
                :to="{ name: 'attraction-detail', params: { id: post.attraction_detail.id } }"
              >
                {{ post.attraction_detail.name }}
              </RouterLink>
            </div>

            <div class="post-article-block">
              <p class="post-content">{{ post.content }}</p>
            </div>

            <div class="post-actions post-actions-elevated">
              <div class="post-action-group">
                <button class="btn btn-primary" type="button" :disabled="!authState.user" @click="handleLike">
                  {{ post.liked ? "已点赞" : "点赞" }} {{ post.likes_count }}
                </button>
                <button class="btn btn-secondary" type="button" :disabled="!authState.user" @click="handleFavorite">
                  {{ post.favorited ? "已收藏" : "收藏" }} {{ post.favorite_count }}
                </button>
              </div>
              <span class="muted">{{ authState.user ? "登录状态下可直接点赞、收藏和评论。" : "登录后可以点赞、收藏和评论。" }}</span>
            </div>
          </div>
        </article>

        <aside class="grid post-detail-side">
          <article class="card section-shell">
            <SectionHeader title="帖子线索" description="把城市、景点和互动信息拆开，阅读时更清楚。" />
            <div class="grid" style="margin-top: 20px">
              <div class="timeline-item">
                <strong>所属城市</strong>
                <p class="muted">{{ post.city_detail?.name || "未关联城市" }}</p>
              </div>
              <div class="timeline-item">
                <strong>关联景点</strong>
                <p class="muted">{{ post.attraction_detail?.name || "未关联景点" }}</p>
              </div>
              <div class="timeline-item">
                <strong>互动情况</strong>
                <p class="muted">
                  浏览 {{ post.views_count }}，点赞 {{ post.likes_count }}，收藏 {{ post.favorite_count }}，评论 {{ totalComments }}
                </p>
              </div>
            </div>
          </article>

          <article class="card section-shell">
            <SectionHeader title="继续浏览" description="从帖子回到社区或继续看景点详情。" />
            <div class="grid" style="margin-top: 20px">
              <RouterLink v-if="post.city_detail" class="btn btn-secondary" :to="{ name: 'community', query: { cityId: post.city_detail.id } }">
                看同城更多内容
              </RouterLink>
              <RouterLink
                v-if="post.attraction_detail"
                class="btn btn-secondary"
                :to="{ name: 'attraction-detail', params: { id: post.attraction_detail.id } }"
              >
                进入景点详情
              </RouterLink>
            </div>
          </article>
        </aside>
      </div>

      <article class="card section-shell">
        <SectionHeader title="评论区" description="支持主评论和回复评论，阅读节奏更接近完整的社区内容页。" />
        <form class="grid comment-composer" style="margin-top: 18px" @submit.prevent="handleComment">
          <textarea
            v-model.trim="commentContent"
            class="textarea"
            rows="5"
            placeholder="写下你的旅行经验、避坑提醒，或者补充这篇帖子的路线信息"
          ></textarea>
          <div class="title-row compact-row">
            <p class="muted auth-inline-note">{{ authState.user ? "评论会立即刷新到当前帖子下。" : "登录后即可发表评论。" }}</p>
            <button class="btn btn-primary" type="submit" :disabled="!authState.user || !commentContent">发表评论</button>
          </div>
        </form>

        <div v-if="post.comments.length" class="comment-list">
          <div v-for="comment in post.comments" :key="comment.id" class="comment-card">
            <div class="comment-card-head">
              <strong>{{ comment.author.nickname }}</strong>
              <span class="pill">{{ formatDate(comment.created_at) }}</span>
            </div>
            <p class="muted">{{ comment.content }}</p>
            <div v-if="comment.replies?.length" class="comment-reply-list">
              <div v-for="reply in comment.replies" :key="reply.id" class="mini-spot comment-reply-card">
                <div class="comment-card-head">
                  <strong>{{ reply.author.nickname }}</strong>
                  <span class="pill">{{ formatDate(reply.created_at) }}</span>
                </div>
                <p class="muted">{{ reply.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="timeline-item" style="margin-top: 22px">
          <strong>还没有评论</strong>
          <p class="muted">可以先补充这篇内容的实际体验、预算或拍照建议。</p>
        </div>
      </article>
    </template>

    <article v-else class="card section-shell page-state">
      <strong>{{ loading ? "正在加载帖子详情..." : "帖子详情暂时不可用" }}</strong>
      <p class="muted">{{ errorMessage || "请稍后重试，或者先返回社区继续浏览。" }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import PageBackButton from "../components/PageBackButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { addComment, getPost, toggleFavorite, toggleLike } from "../services/api";
import { authState } from "../stores/auth";


const route = useRoute();
const post = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const commentContent = ref("");
let requestId = 0;

const totalComments = computed(() => {
  if (!post.value?.comments?.length) return 0;
  return post.value.comments.reduce((count, item) => count + 1 + (item.replies?.length || 0), 0);
});

const postCoverStyle = computed(() => ({
  backgroundImage: post.value?.cover_image
    ? `linear-gradient(135deg, rgba(10, 42, 53, 0.36), rgba(10, 42, 53, 0.7)), url(${post.value.cover_image})`
    : "linear-gradient(135deg, rgba(13, 92, 99, 0.92), rgba(27, 73, 101, 0.88))",
}));

function formatDate(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "";
}

async function loadPost(id = route.params.id) {
  if (!id) return;
  const currentRequestId = ++requestId;
  loading.value = true;
  errorMessage.value = "";
  post.value = null;

  try {
    const data = await getPost(id);
    if (currentRequestId !== requestId) return;
    post.value = data;
  } catch (error) {
    if (currentRequestId !== requestId) return;
    errorMessage.value = error.response?.data?.detail || "帖子详情加载失败。";
  } finally {
    if (currentRequestId === requestId) {
      loading.value = false;
    }
  }
}

async function handleLike() {
  if (!authState.user) return;
  const data = await toggleLike(route.params.id);
  post.value = {
    ...post.value,
    liked: data.liked,
    likes_count: data.likes_count,
  };
}

async function handleFavorite() {
  if (!authState.user) return;
  const data = await toggleFavorite(route.params.id);
  post.value = {
    ...post.value,
    favorited: data.favorited,
    favorite_count: data.favorite_count,
  };
}

async function handleComment() {
  if (!authState.user || !commentContent.value) return;
  post.value = await addComment(route.params.id, { content: commentContent.value });
  commentContent.value = "";
}

watch(
  () => route.params.id,
  (id) => {
    commentContent.value = "";
    loadPost(id);
  },
  { immediate: true },
);
</script>
