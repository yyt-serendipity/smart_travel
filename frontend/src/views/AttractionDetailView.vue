<template>
  <section class="page">
    <div class="page-toolbar">
      <PageBackButton :fallback-to="backLink" label="返回上一页" />
      <div class="action-row">
        <RouterLink v-if="attraction?.city_detail" class="btn btn-secondary" :to="backLink">所属城市</RouterLink>
        <RouterLink
          v-if="attraction?.city_detail"
          class="btn btn-primary"
          :to="{ name: 'planner', query: { targetCity: attraction.city_detail.name, cityId: attraction.city_detail.id } }"
        >
          按景点做路线
        </RouterLink>
      </div>
    </div>

    <template v-if="attraction">
      <article class="card detail-banner" :style="bannerStyle">
        <div class="detail-overlay">
          <span class="eyebrow">Attraction</span>
          <h1 class="hero-title">{{ attraction.name }}</h1>
          <p class="hero-subtitle">{{ attraction.description || attraction.address || "景点详情已整理为结构化信息。" }}</p>
          <div class="chip-row">
            <span v-if="attraction.city_detail" class="pill">{{ attraction.city_detail.name }}</span>
            <span v-if="attraction.rating" class="pill">评分 {{ attraction.rating }}</span>
            <span v-if="attraction.suggested_play_time" class="pill">{{ attraction.suggested_play_time }}</span>
            <span v-if="attraction.best_season" class="pill">{{ attraction.best_season }}</span>
          </div>
        </div>
      </article>

      <div class="grid grid-2">
        <article class="card section-shell">
          <SectionHeader title="景点信息" description="门票、开放时间、地址和小贴士都在这里，方便直接做行程。" />
          <div class="info-list" style="margin-top: 20px">
            <div class="timeline-item">
              <strong>地址</strong>
              <p class="muted">{{ attraction.address || "暂无地址信息" }}</p>
            </div>
            <div class="timeline-item">
              <strong>开放时间</strong>
              <p class="muted">{{ attraction.opening_hours || "暂无开放时间说明" }}</p>
            </div>
            <div class="timeline-item">
              <strong>门票信息</strong>
              <p class="muted">{{ attraction.ticket_info || "暂无门票说明" }}</p>
            </div>
            <div class="timeline-item">
              <strong>游玩建议</strong>
              <p class="muted">{{ attraction.tips || "暂时没有额外提示，可以先结合 AI 行程查看。" }}</p>
            </div>
          </div>
        </article>

        <article class="card section-shell">
          <SectionHeader title="关联入口" description="从景点详情页继续回到城市、社区或来源页面。" />
          <div class="grid" style="margin-top: 20px">
            <RouterLink
              v-if="attraction.city_detail"
              class="btn btn-secondary"
              :to="{ name: 'city-detail', params: { id: attraction.city_detail.id } }"
            >
              查看所属城市
            </RouterLink>
            <RouterLink
              v-if="attraction.city_detail"
              class="btn btn-secondary"
              :to="{ name: 'community', query: { cityId: attraction.city_detail.id } }"
            >
              查看同城帖子
            </RouterLink>
            <a v-if="attraction.source_url" class="btn btn-secondary" :href="attraction.source_url" target="_blank" rel="noreferrer">
              查看来源页面
            </a>
          </div>
        </article>
      </div>

      <article class="card section-shell">
        <div class="title-row">
          <SectionHeader title="相关社区帖子" description="优先显示和该景点直接关联的帖子，没有时自动回退到同城内容。" />
          <RouterLink
            v-if="attraction.city_detail"
            class="btn btn-secondary"
            :to="{ name: 'community', query: { cityId: attraction.city_detail.id } }"
          >
            进入社区
          </RouterLink>
        </div>
        <div v-if="relatedPosts.length" class="grid grid-3" style="margin-top: 24px">
          <PostCard v-for="post in relatedPosts" :key="post.id" :post="post" />
        </div>
        <div v-else class="timeline-item" style="margin-top: 24px">
          <strong>暂时没有相关帖子</strong>
          <p class="muted">可以先进入社区发布这处景点的体验内容。</p>
        </div>
      </article>
    </template>

    <article v-else class="card section-shell page-state">
      <strong>{{ loading ? "正在加载景点详情..." : "景点详情暂时不可用" }}</strong>
      <p class="muted">{{ errorMessage || "请稍后重试，或者先返回城市列表继续浏览。" }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import PageBackButton from "../components/PageBackButton.vue";
import PostCard from "../components/PostCard.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { getAttraction, getPosts } from "../services/api";


const route = useRoute();
const attraction = ref(null);
const relatedPosts = ref([]);
const loading = ref(false);
const errorMessage = ref("");
let requestId = 0;

const bannerStyle = computed(() => ({
  background: attraction.value?.image_url
    ? `linear-gradient(180deg, rgba(9, 26, 37, 0.08), rgba(9, 26, 37, 0.82)), url(${attraction.value.image_url}) center/cover`
    : "linear-gradient(135deg, #114b5f, #1a936f 55%, #f1a208)",
}));

const backLink = computed(() => {
  if (attraction.value?.city_detail) {
    return { name: "city-detail", params: { id: attraction.value.city_detail.id } };
  }
  return { name: "cities" };
});

async function loadAttraction(id) {
  if (!id) return;
  const currentRequestId = ++requestId;
  loading.value = true;
  errorMessage.value = "";
  attraction.value = null;
  relatedPosts.value = [];

  try {
    const detail = await getAttraction(id);
    if (currentRequestId !== requestId) return;
    attraction.value = detail;

    let posts = await getPosts({ attraction_id: id });
    if (currentRequestId !== requestId) return;
    if (!posts.length && detail.city) {
      posts = await getPosts({ city_id: detail.city });
      if (currentRequestId !== requestId) return;
    }
    relatedPosts.value = posts;
  } catch (error) {
    if (currentRequestId !== requestId) return;
    errorMessage.value = error.response?.data?.detail || "景点详情加载失败。";
  } finally {
    if (currentRequestId === requestId) {
      loading.value = false;
    }
  }
}

watch(() => route.params.id, loadAttraction, { immediate: true });
</script>
