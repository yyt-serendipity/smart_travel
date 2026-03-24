<template>
  <section class="page">
    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader title="景点总览" description="按关键词、城市和标签筛选景点。" />
        <span class="pill">{{ attractions.length }} 个景点</span>
      </div>

      <div class="field-grid" style="margin-top: 24px">
        <div class="field">
          <label for="attractionKeyword">关键词</label>
          <input id="attractionKeyword" v-model.trim="keyword" placeholder="搜索景点" />
        </div>
        <div class="field">
          <label for="attractionProvince">省份</label>
          <select id="attractionProvince" v-model="province">
            <option value="">全部省份</option>
            <option v-for="item in provinceOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </div>
        <div class="field">
          <label for="attractionCity">城市</label>
          <select id="attractionCity" v-model="selectedCityId">
            <option value="">全部城市</option>
            <option v-for="city in filteredCityOptions" :key="city.id" :value="String(city.id)">{{ city.name }}</option>
          </select>
        </div>
        <div class="field">
          <label>标签</label>
          <select v-model="selectedTag">
            <option v-for="tag in tagOptions" :key="tag" :value="tag">{{ tag }}</option>
          </select>
        </div>
      </div>
    </article>

    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader title="景点列表" description="简介过长可展开，卡片底部直接进入详情。" />
        <RouterLink v-if="selectedCityDetail" class="btn btn-secondary" :to="{ name: 'city-detail', params: { id: selectedCityDetail.id } }">
          进入 {{ selectedCityDetail.name }}
        </RouterLink>
      </div>

      <div v-if="loading && !attractions.length" class="page-state" style="margin-top: 24px">
        <strong>正在加载景点...</strong>
      </div>
      <div v-else-if="!attractions.length" class="page-state" style="margin-top: 24px">
        <strong>没有匹配的景点</strong>
      </div>
      <template v-else>
        <div class="grid grid-3" style="margin-top: 24px">
          <AttractionCard v-for="attraction in visibleAttractions" :key="attraction.id" :attraction="attraction" :expandable="true" />
        </div>
        <div ref="sentinelRef" class="list-lazy-sentinel">
          <span class="pill">{{ visibleAttractions.length }} / {{ attractions.length }}</span>
        </div>
      </template>
    </article>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AttractionCard from "../components/AttractionCard.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { getAttractions, getCities } from "../services/api";
import { normalizeProvince } from "../utils/mapData";


const PAGE_SIZE = 12;

const route = useRoute();
const router = useRouter();
const keyword = ref(route.query.q || "");
const province = ref(route.query.province || "");
const selectedCityId = ref(route.query.cityId ? String(route.query.cityId) : "");
const selectedTag = ref(route.query.tag || "全部");
const cityOptions = ref([]);
const attractions = ref([]);
const loading = ref(false);
const visibleCount = ref(PAGE_SIZE);
const sentinelRef = ref(null);
let observer = null;

const provinceOptions = computed(() => {
  const names = new Set(cityOptions.value.map((item) => normalizeProvince(item.province)));
  return [...names].filter((item) => item !== "未分省").sort();
});

const filteredCityOptions = computed(() => {
  if (!province.value) return cityOptions.value;
  return cityOptions.value.filter((item) => normalizeProvince(item.province) === province.value);
});

const tagOptions = computed(() => {
  const tagSet = new Set(["全部"]);
  attractions.value.forEach((item) => {
    (item.tags || []).forEach((tag) => tagSet.add(tag));
  });
  return [...tagSet];
});

const selectedCityDetail = computed(() => cityOptions.value.find((item) => String(item.id) === selectedCityId.value) || null);
const visibleAttractions = computed(() => attractions.value.slice(0, visibleCount.value));

function resetVisibleCount() {
  visibleCount.value = PAGE_SIZE;
}

function loadMore() {
  if (visibleCount.value >= attractions.value.length) return;
  visibleCount.value += PAGE_SIZE;
}

async function setupObserver() {
  await nextTick();
  if (observer) observer.disconnect();
  if (!sentinelRef.value) return;

  observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      loadMore();
    }
  });
  observer.observe(sentinelRef.value);
}

async function loadCities() {
  cityOptions.value = await getCities({ limit: 500 });
}

async function loadAttractions() {
  loading.value = true;
  try {
    attractions.value = await getAttractions({
      q: keyword.value || undefined,
      province: province.value || undefined,
      city_id: selectedCityId.value || undefined,
      tag: selectedTag.value !== "全部" ? selectedTag.value : undefined,
      limit: 120,
    });
  } finally {
    loading.value = false;
  }
  resetVisibleCount();
  await setupObserver();
}

function syncQuery() {
  router.replace({
    name: "attractions",
    query: {
      q: keyword.value || undefined,
      province: province.value || undefined,
      cityId: selectedCityId.value || undefined,
      tag: selectedTag.value !== "全部" ? selectedTag.value : undefined,
    },
  });
}

watch(province, () => {
  if (selectedCityId.value && !filteredCityOptions.value.some((item) => String(item.id) === selectedCityId.value)) {
    selectedCityId.value = "";
  }
});

watch([keyword, province, selectedCityId, selectedTag], async () => {
  syncQuery();
  await loadAttractions();
});

watch(
  () => route.query,
  (query) => {
    keyword.value = query.q || "";
    province.value = query.province || "";
    selectedCityId.value = query.cityId ? String(query.cityId) : "";
    selectedTag.value = query.tag || "全部";
  },
);

onMounted(async () => {
  await loadCities();
  await loadAttractions();
});

onBeforeUnmount(() => {
  observer?.disconnect();
});
</script>
