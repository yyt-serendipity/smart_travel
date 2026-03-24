<template>
  <section class="page home-page">
    <HomeHeroCarousel :slides="carouselSlides" />

    <article class="card section-shell stat-strip">
      <div class="stat-strip-item">
        <span class="muted">覆盖省份</span>
        <strong>{{ provinceStats.length }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">收录城市</span>
        <strong>{{ allCities.length }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">收录景点</span>
        <strong>{{ totalAttractionCount }}</strong>
      </div>
      <div class="stat-strip-item">
        <span class="muted">最新帖子</span>
        <strong>{{ overview.latest_posts.length }}</strong>
      </div>
    </article>

    <ProvinceInspirationMap :provinces="provinceStats" :loading="loading" />

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader
          :title="overview.recommendation.spotlight_title"
          description="优先展示更适合当前用户偏好和常住城市的景点卡片。"
        />
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
          description="从城市热度、景点密度和标签风格里挑出更值得先看的入口城市。"
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
import ProvinceInspirationMap from "../components/home/ProvinceInspirationMap.vue";
import { getCities, getOverview } from "../services/api";
import { buildProvinceStats } from "../utils/mapData";

const loading = ref(true);
const allCities = ref([]);
const overview = ref({
  hero: {
    title: "围绕中国城市、景点与旅行内容建立的智能旅游平台",
    subtitle: "把景点资料、AI 行程、社区帖子和个人收藏整合到一套连续的浏览体验里。",
  },
  recommendation: {
    is_personalized: false,
    home_city: null,
    favorite_styles: [],
    spotlight_title: "热门景点精选",
    city_title: "城市推荐",
  },
  featured_cities: [],
  spotlight_attractions: [],
  latest_posts: [],
});

const provinceStats = computed(() => buildProvinceStats(allCities.value));
const totalAttractionCount = computed(() =>
  allCities.value.reduce((sum, city) => sum + Number(city.attraction_count || 0), 0),
);

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

onMounted(async () => {
  try {
    const [overviewData, cities] = await Promise.all([getOverview(), getCities({ limit: 500 })]);
    overview.value = overviewData;
    allCities.value = cities;
  } finally {
    loading.value = false;
  }
});
</script>
