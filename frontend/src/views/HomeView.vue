<template>
  <section class="page home-page">
    <HomeHeroCarousel :slides="carouselSlides" />

    <article class="card section-shell stat-strip">
      <div class="stat-strip-item">
        <span class="muted">覆盖省份</span>
        <strong>{{ overview.stats.provinceCount }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">收录城市</span>
        <strong>{{ overview.stats.cityCount }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">收录景点</span>
        <strong>{{ overview.stats.attractionCount }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">最新帖子</span>
        <strong>{{ overview.stats.latestPostCount }}</strong>
      </div>
    </article>

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader title="省域旅行灵感" description="先从省份入口浏览，再进入对应城市和景点内容。" />
        <RouterLink class="btn btn-secondary" to="/cities">全部城市</RouterLink>
      </div>

      <div v-if="loading && !overview.province_cards.length" class="page-state" style="margin-top: 24px">
        <strong>正在加载省份入口...</strong>
      </div>
      <div v-else class="province-showcase-grid" style="margin-top: 24px">
        <RouterLink
          v-for="province in overview.province_cards"
          :key="province.province"
          class="province-showcase-card"
          :to="{ name: 'cities', query: { province: province.province } }"
        >
          <div class="province-showcase-cover" :style="provinceCoverStyle(province)">
            <span v-if="province.averageRating" class="province-rating-badge province-rating-corner">
              <span class="province-rating-star">★</span>
              <strong>{{ province.averageRating }}</strong>
            </span>
          </div>
          <div class="province-showcase-copy">
            <div class="title-row compact-row">
              <strong>{{ province.shortName }}</strong>
              <span class="pill">{{ province.cityCount }} 城市</span>
            </div>
            <p class="muted province-entry-line">
              主入口城市：{{ province.topCity?.name || "待补充" }}，{{ province.attractionCount }} 景点
            </p>
            <div class="chip-row province-showcase-meta">
              <span
                v-for="tag in (province.topCity?.tags || []).slice(0, 3)"
                :key="`${province.province}-${tag}`"
                class="tag-pill"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </RouterLink>
      </div>
    </article>

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader
          :title="overview.recommendation.spotlight_title"
          :description="overview.recommendation.spotlight_description"
        />
        <span v-if="personalizing" class="pill">正在更新个性化推荐</span>
        <RouterLink class="btn btn-secondary" to="/attractions">景点总览</RouterLink>
      </div>

      <div v-if="loading && !overview.spotlight_attractions.length" class="page-state" style="margin-top: 24px">
        <strong>正在加载景点推荐...</strong>
      </div>
      <div v-else class="grid grid-4" style="margin-top: 24px">
        <AttractionCard
          v-for="attraction in overview.spotlight_attractions"
          :key="attraction.id"
          :attraction="attraction"
          :expandable="true"
        />
      </div>
    </article>

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader
          :title="overview.recommendation.city_title"
          :description="overview.recommendation.city_description"
        />
        <RouterLink class="btn btn-secondary" to="/cities">全部城市</RouterLink>
      </div>

      <div v-if="loading && !overview.featured_cities.length" class="page-state" style="margin-top: 24px">
        <strong>正在加载城市推荐...</strong>
      </div>
      <div v-else class="grid grid-4" style="margin-top: 24px">
        <CityCard v-for="city in overview.featured_cities" :key="city.id" :city="city" />
      </div>
    </article>

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader title="最新帖子" description="看真实体验、路线记录和避坑建议，快速找到值得参考的内容。" />
        <RouterLink class="btn btn-secondary" to="/community">进入社区</RouterLink>
      </div>

      <div v-if="loading && !overview.latest_posts.length" class="page-state" style="margin-top: 24px">
        <strong>正在加载社区内容...</strong>
      </div>
      <div v-else class="grid grid-2" style="margin-top: 24px">
        <PostCard v-for="post in overview.latest_posts" :key="post.id" :post="post" />
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import AttractionCard from "../components/AttractionCard.vue";
import CityCard from "../components/CityCard.vue";
import PostCard from "../components/PostCard.vue";
import SectionHeader from "../components/SectionHeader.vue";
import HomeHeroCarousel from "../components/home/HomeHeroCarousel.vue";
import { getOverview } from "../services/api";
import { authState } from "../stores/auth";

const loading = ref(true);
const personalizing = ref(false);
const overview = ref({
  hero: {
    title: "围绕中国城市、景点与旅行内容建立的智能旅游平台",
    subtitle: "把景点资料、AI 行程、社区帖子和个人收藏整合到一套连续的浏览体验里。",
  },
  stats: {
    provinceCount: 0,
    cityCount: 0,
    attractionCount: 0,
    latestPostCount: 0,
  },
  province_cards: [],
  recommendation: {
    is_personalized: false,
    home_city: null,
    favorite_styles: [],
    spotlight_title: "热门景点精选",
    spotlight_description: "先展示默认 TOPSIS 推荐。",
    city_title: "城市推荐",
    city_description: "先展示默认城市入口。",
  },
  featured_cities: [],
  spotlight_attractions: [],
  latest_posts: [],
});

const carouselSlides = computed(() =>
  overview.value.featured_cities.slice(0, 4).map((city) => ({
    key: `city-${city.id}`,
    title: city.name,
    description: city.short_intro || "直接进入城市详情。",
    image: city.cover_image,
    meta: [`${city.recommended_days || 3} 天游`, `${city.attraction_count || 0} 景点`, ...(city.tags?.slice(0, 2) || [])],
    actionLabel: "查看城市详情",
    to: { name: "city-detail", params: { id: city.id } },
  })),
);

function provinceCoverStyle(province) {
  const image = province.topCity?.cover_image;
  return {
    background: image
      ? `linear-gradient(180deg, rgba(10, 37, 46, 0.14), rgba(10, 37, 46, 0.72)), url(${image}) center/cover`
      : "linear-gradient(135deg, #0d5c63, #1b4965 58%, #f28f3b)",
  };
}

onMounted(async () => {
  try {
    overview.value = await getOverview({ mode: "default" });
    loading.value = false;
    if (authState.token) {
      personalizing.value = true;
      try {
        overview.value = await getOverview({ mode: "personalized" });
      } catch (error) {
        console.error("Failed to load personalized home recommendations.", error);
      } finally {
        personalizing.value = false;
      }
    }
  } finally {
    loading.value = false;
  }
});
</script>
