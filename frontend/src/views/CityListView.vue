<template>
  <section class="page">
    <article class="card section-shell">
      <div class="title-row">
        <SectionHeader eyebrow="Cities" title="城市推荐" description="按关键词、省份和标签筛选城市，列表会继续懒加载展开。" />
        <span class="pill">{{ filteredCities.length }} 个目的地</span>
      </div>

      <div class="field-grid" style="margin-top: 24px">
        <div class="field">
          <label for="keyword">关键词</label>
          <input id="keyword" v-model.trim="keyword" placeholder="搜索城市或省份" />
        </div>
        <div class="field">
          <label for="province">省份</label>
          <select id="province" v-model="selectedProvince">
            <option value="">全部省份</option>
            <option v-for="item in provinceOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </div>
      </div>

      <div class="chip-row" style="margin-top: 18px">
        <button
          v-for="tag in tags"
          :key="tag"
          class="chip"
          :class="{ active: selectedTag === tag }"
          type="button"
          @click="selectedTag = tag"
        >
          {{ tag }}
        </button>
      </div>
    </article>

    <article class="card section-shell">
      <div v-if="loading && !filteredCities.length" class="page-state">
        <strong>正在加载城市列表...</strong>
      </div>
      <div v-else-if="!filteredCities.length" class="page-state">
        <strong>没有匹配的城市</strong>
      </div>
      <template v-else>
        <div class="grid grid-3">
          <CityCard v-for="city in visibleCities" :key="city.id" :city="city" />
        </div>
        <div ref="sentinelRef" class="list-lazy-sentinel">
          <span class="pill">{{ visibleCities.length }} / {{ filteredCities.length }}</span>
        </div>
      </template>
    </article>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import CityCard from "../components/CityCard.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { getCities } from "../services/api";
import { dedupeTags, normalizeProvince } from "../utils/mapData";


const PAGE_SIZE = 12;

const route = useRoute();
const router = useRouter();
const keyword = ref(route.query.q || "");
const selectedProvince = ref(route.query.province || "");
const selectedTag = ref(route.query.tag || "全部");
const cityList = ref([]);
const loading = ref(false);
const visibleCount = ref(PAGE_SIZE);
const sentinelRef = ref(null);
let observer = null;

const provinceOptions = computed(() => {
  const provinces = new Set(cityList.value.map((item) => normalizeProvince(item.province)));
  return [...provinces].filter((item) => item !== "未分省").sort();
});

const tagSourceCities = computed(() =>
  cityList.value.filter((city) => {
    const hitKeyword =
      !keyword.value ||
      [city.name, city.province, city.short_intro, city.overview].some((item) => String(item || "").includes(keyword.value));
    const hitProvince = !selectedProvince.value || normalizeProvince(city.province) === selectedProvince.value;
    return hitKeyword && hitProvince;
  }),
);

const filteredCities = computed(() =>
  tagSourceCities.value.filter((city) => selectedTag.value === "全部" || (city.tags || []).includes(selectedTag.value)),
);

const visibleCities = computed(() => filteredCities.value.slice(0, visibleCount.value));
const tags = computed(() => ["全部", ...dedupeTags(tagSourceCities.value).sort((a, b) => a.localeCompare(b, "zh-CN"))]);

function resetVisibleCount() {
  visibleCount.value = PAGE_SIZE;
}

function loadMore() {
  if (visibleCount.value >= filteredCities.value.length) return;
  visibleCount.value += PAGE_SIZE;
}

async function setupObserver() {
  await nextTick();
  if (observer) {
    observer.disconnect();
  }
  if (!sentinelRef.value) return;

  observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      loadMore();
    }
  });
  observer.observe(sentinelRef.value);
}

function syncQuery() {
  router.replace({
    name: "cities",
    query: {
      q: keyword.value || undefined,
      province: selectedProvince.value || undefined,
      tag: selectedTag.value !== "全部" ? selectedTag.value : undefined,
    },
  });
}

watch(
  () => route.query,
  (query) => {
    keyword.value = query.q || "";
    selectedProvince.value = query.province || "";
    selectedTag.value = query.tag || "全部";
  },
);

watch([keyword, selectedProvince, selectedTag], async () => {
  if (selectedTag.value !== "全部" && !tags.value.includes(selectedTag.value)) {
    selectedTag.value = "全部";
  }
  resetVisibleCount();
  syncQuery();
  await setupObserver();
});

watch(filteredCities, async () => {
  resetVisibleCount();
  await setupObserver();
});

onMounted(async () => {
  loading.value = true;
  try {
    cityList.value = await getCities({ limit: 500 });
  } finally {
    loading.value = false;
  }
  await setupObserver();
});

onBeforeUnmount(() => {
  observer?.disconnect();
});
</script>
