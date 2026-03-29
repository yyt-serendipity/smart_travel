<template>
  <section class="page">
    <div class="page-toolbar">
      <PageBackButton :fallback-to="{ name: 'cities' }" label="返回城市列表" />
      <RouterLink class="btn btn-secondary" :to="{ name: 'cities', query: city?.province ? { province: city.province } : {} }">
        返回同省城市
      </RouterLink>
    </div>

    <template v-if="city">
      <div class="city-detail-layout">
        <aside class="card section-shell city-detail-side-panel">
          <div class="city-side-cover" :style="coverStyle"></div>
          <div class="grid">
            <div>
              <span class="eyebrow">{{ city.province || '中国' }}</span>
              <h1 class="section-title city-side-title">{{ city.name }}</h1>
              <p class="muted">{{ city.overview || city.short_intro }}</p>
            </div>

            <section class="city-weather-panel">
              <div class="title-row compact-row">
                <div>
                  <span class="eyebrow">最近天气</span>
                </div>
                <span v-if="weather?.report_time" class="pill">更新 {{ weather.report_time.slice(5, 16) }}</span>
              </div>

              <p v-if="weatherLoading" class="muted">正在同步高德天气...</p>
              <p v-else-if="weatherError" class="muted">{{ weatherError }}</p>

              <template v-else-if="weather">
                <div class="city-weather-now">
                  <div>
                    <p class="city-weather-caption">实时天气</p>
                    <strong>{{ weather.current.weather || weather.forecast[0]?.day_weather || '天气待更新' }}</strong>
                    <p class="muted">
                      {{ weather.current.temperature ? `${weather.current.temperature}°C` : '温度待更新' }}
                      <template v-if="weather.current.humidity"> · 湿度 {{ weather.current.humidity }}%</template>
                    </p>
                  </div>
                  <div class="city-weather-icon" aria-hidden="true">
                    {{ weatherSymbol(weather.current.weather || weather.forecast[0]?.day_weather) }}
                  </div>
                </div>

                <div class="city-weather-grid">
                  <article v-for="item in weather.forecast" :key="item.date" class="city-weather-day-card">
                    <span>{{ item.week_label || formatWeatherDate(item.date) }}</span>
                    <strong>{{ weatherSymbol(item.day_weather) }} {{ item.day_weather || '未知' }}</strong>
                    <p>夜间 {{ item.night_weather || item.day_weather || '未知' }}</p>
                    <div class="city-weather-temps">
                      <span>{{ item.day_temp }}°</span>
                      <span>{{ item.night_temp }}°</span>
                    </div>
                  </article>
                </div>
              </template>
            </section>

            <section class="city-map-panel">
              <div class="title-row compact-row">
                <div>
                  <span class="eyebrow">高德定位</span>
                </div>
                <a class="city-map-link" :href="amapExploreUrl" target="_blank" rel="noreferrer">在高德查看</a>
              </div>

              <div v-if="staticMapUrl && !mapLoadFailed" class="city-static-map-frame">
                <img :src="staticMapUrl" :alt="`${city.name} 静态地图`" loading="lazy" @error="mapLoadFailed = true" />
              </div>
              <p v-else class="muted">静态地图暂时不可用，可稍后重试或直接在高德地图中查看。</p>
            </section>

            <div class="chip-row">
              <span class="pill">{{ city.recommended_days }} 天游玩</span>
              <span class="pill">{{ city.attraction_count }} 个景点</span>
              <span v-if="city.average_rating" class="pill">评分 {{ city.average_rating }}</span>
              <span v-if="city.best_season" class="pill">{{ city.best_season }}</span>
            </div>

            <div class="timeline-item">
              <strong>城市亮点</strong>
              <p class="muted">{{ city.travel_highlights || city.short_intro || '暂未补充城市亮点。' }}</p>
            </div>

            <div class="timeline-item">
              <strong>出行建议</strong>
              <p class="muted">{{ city.travel_tips || '可以先从右侧景点导览卡里挑一个评分更高的景点开始浏览。' }}</p>
            </div>

            <div class="action-row">
              <RouterLink class="btn btn-primary" :to="{ name: 'planner', query: { targetCity: city.name } }">为这座城市生成行程</RouterLink>
              <RouterLink class="btn btn-secondary" :to="{ name: 'community', query: { cityId: city.id } }">查看同城帖子</RouterLink>
            </div>
          </div>
        </aside>

        <div class="grid city-detail-main">
          <article class="card section-shell">
            <div class="title-row">
              <SectionHeader
                title="景点导览"
                description="这里改成图文导览，先看大图和摘要，再切换到想深入了解的景点。"
              />
              <span class="pill">可选 {{ city.attractions.length }} 个景点</span>
            </div>

            <div v-if="activeAttraction" class="city-spotlight-shell" style="margin-top: 22px">
              <div class="city-spotlight-hero" :style="activeAttractionStyle">
                <div class="city-spotlight-overlay">
                  <span class="eyebrow">Spotlight</span>
                  <h2 class="section-title">{{ activeAttraction.name }}</h2>
                  <div class="city-spotlight-description">
                    <ExpandableText
                      :text="activeAttraction.description || activeAttraction.address"
                      empty-text="这处景点的详细介绍还在持续补充中。"
                      :lines="7"
                      :min-length="120"
                      tone="light"
                    />
                  </div>
                  <div class="chip-row">
                    <span v-if="activeAttraction.rating" class="pill">评分 {{ activeAttraction.rating }}</span>
                    <span v-if="activeAttraction.suggested_play_time" class="pill">{{ activeAttraction.suggested_play_time }}</span>
                    <span v-if="activeAttraction.best_season" class="pill">{{ activeAttraction.best_season }}</span>
                  </div>
                  <RouterLink class="btn btn-primary" :to="{ name: 'attraction-detail', params: { id: activeAttraction.id } }">
                    查看景点详情
                  </RouterLink>
                </div>
              </div>

              <div class="city-spotlight-list">
                <article
                  v-for="attraction in city.attractions"
                  :key="attraction.id"
                  class="city-spotlight-item"
                  :class="{ active: activeAttractionId === attraction.id }"
                  tabindex="0"
                  role="button"
                  @click="handleSelectAttraction(attraction)"
                  @keydown.enter="handleSelectAttraction(attraction)"
                  @keydown.space.prevent="handleSelectAttraction(attraction)"
                >
                  <div class="title-row compact-row">
                    <strong>{{ attraction.name }}</strong>
                    <span class="pill">{{ attraction.rating || '推荐' }}</span>
                  </div>
                  <ExpandableText
                    :text="attraction.description || attraction.address"
                    empty-text="景点资料待补充。"
                    :min-length="48"
                  />
                  <div class="chip-row">
                    <span v-if="attraction.suggested_play_time" class="pill">{{ attraction.suggested_play_time }}</span>
                    <span v-if="attraction.best_season" class="pill">{{ attraction.best_season }}</span>
                  </div>
                </article>
              </div>
            </div>
          </article>

          <article class="card section-shell">
            <div class="title-row">
              <SectionHeader title="核心景点" description="下面保留完整卡片列表，方便直接跳转、筛选和继续浏览。" />
              <RouterLink class="btn btn-secondary" :to="{ name: 'attractions', query: { cityId: city.id } }">看该城市全部景点</RouterLink>
            </div>
            <div class="grid grid-3" style="margin-top: 24px">
              <AttractionCard
                v-for="attraction in city.attractions"
                :key="attraction.id"
                :attraction="attraction"
                :city-name="city.name"
              />
            </div>
          </article>
        </div>
      </div>
    </template>

    <article v-else class="card section-shell page-state">
      <strong>{{ loading ? '正在加载城市详情...' : '城市详情暂时不可用' }}</strong>
      <p class="muted">{{ errorMessage || '请稍后重试，或者先返回城市列表继续浏览。' }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AttractionCard from "../components/AttractionCard.vue";
import ExpandableText from "../components/ExpandableText.vue";
import PageBackButton from "../components/PageBackButton.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { getCity, getCityWeather } from "../services/api";

const route = useRoute();
const city = ref(null);
const loading = ref(false);
const errorMessage = ref("");
const weather = ref(null);
const weatherLoading = ref(false);
const weatherError = ref("");
const mapLoadFailed = ref(false);
const activeAttractionId = ref(null);
let requestId = 0;

const coverStyle = computed(() => ({
  background: city.value?.cover_image
    ? `linear-gradient(180deg, rgba(10, 40, 48, 0.08), rgba(10, 40, 48, 0.54)), url(${city.value.cover_image}) center/cover`
    : "linear-gradient(135deg, #0d5c63, #1b4965 55%, #f28f3b)",
}));

const activeAttraction = computed(
  () => city.value?.attractions?.find((item) => item.id === activeAttractionId.value) || city.value?.attractions?.[0] || null,
);

const activeAttractionStyle = computed(() => ({
  background: activeAttraction.value?.image_url
    ? `linear-gradient(180deg, rgba(10, 38, 48, 0.16), rgba(10, 38, 48, 0.82)), url(${activeAttraction.value.image_url}) center/cover`
    : "linear-gradient(135deg, #104b56, #1f6f78 55%, #f28f3b)",
}));

const staticMapUrl = computed(() => (city.value ? `/api/cities/${city.value.id}/static-map/` : ""));
const amapExploreUrl = computed(() =>
  city.value ? `https://uri.amap.com/search?keyword=${encodeURIComponent(city.value.name)}` : "#",
);

function handleSelectAttraction(attraction) {
  activeAttractionId.value = attraction.id;
}

function weatherSymbol(text) {
  const value = text || "";
  if (value.includes("雷")) return "⛈";
  if (value.includes("雪")) return "❄";
  if (value.includes("雨")) return "🌧";
  if (value.includes("云") || value.includes("阴")) return "☁";
  if (value.includes("雾")) return "🌫";
  if (value.includes("晴")) return "☀";
  return "🌤";
}

function formatWeatherDate(value) {
  if (!value) return "";
  const segments = value.split("-");
  if (segments.length !== 3) return value;
  return `${segments[1]}/${segments[2]}`;
}

async function loadWeather(id, currentRequestId) {
  if (!id) return;
  weatherLoading.value = true;
  weatherError.value = "";
  weather.value = null;

  try {
    const data = await getCityWeather(id);
    if (currentRequestId !== requestId) return;
    weather.value = data;
  } catch (error) {
    if (currentRequestId !== requestId) return;
    weatherError.value = error.response?.data?.detail || "天气信息暂时不可用。";
  } finally {
    if (currentRequestId === requestId) {
      weatherLoading.value = false;
    }
  }
}

async function loadCity(id) {
  if (!id) return;
  const currentRequestId = ++requestId;
  loading.value = true;
  errorMessage.value = "";
  city.value = null;
  weather.value = null;
  weatherError.value = "";
  mapLoadFailed.value = false;
  loadWeather(id, currentRequestId);

  try {
    const data = await getCity(id);
    if (currentRequestId !== requestId) return;
    city.value = data;
    activeAttractionId.value = data.attractions?.[0]?.id || null;
  } catch (error) {
    if (currentRequestId !== requestId) return;
    errorMessage.value = error.response?.data?.detail || "城市详情加载失败。";
  } finally {
    if (currentRequestId === requestId) {
      loading.value = false;
    }
  }
}

watch(() => route.params.id, loadCity, { immediate: true });
</script>

<style scoped>
.city-weather-panel,
.city-map-panel {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 24px;
  border: 1px solid rgba(17, 57, 68, 0.08);
  background: linear-gradient(180deg, rgba(246, 248, 247, 0.92), rgba(255, 255, 255, 0.98));
}

.city-weather-now {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(14, 71, 80, 0.08), rgba(242, 143, 59, 0.16));
}

.city-weather-caption {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.city-weather-now strong {
  display: block;
  font-size: 28px;
  color: var(--secondary);
}

.city-weather-now p,
.city-weather-day-card p {
  margin: 0;
}

.city-weather-icon {
  font-size: 42px;
  line-height: 1;
}

.city-weather-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.city-weather-day-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(17, 57, 68, 0.08);
  background: rgba(255, 255, 255, 0.92);
}

.city-weather-day-card span {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.city-weather-day-card strong,
.city-map-panel strong {
  color: var(--secondary);
}

.city-weather-day-card p {
  color: var(--muted);
}

.city-weather-temps {
  display: flex;
  gap: 10px;
  font-weight: 700;
  color: var(--secondary);
}

.city-map-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(10, 94, 99, 0.14);
  color: var(--secondary);
  background: rgba(255, 255, 255, 0.82);
}

.city-static-map-frame {
  overflow: hidden;
  min-height: 220px;
  border-radius: 22px;
  border: 1px solid rgba(17, 57, 68, 0.08);
  background: rgba(236, 243, 242, 0.94);
}

.city-static-map-frame img {
  display: block;
  width: 100%;
  height: 100%;
  aspect-ratio: 19 / 9;
  object-fit: cover;
}

@media (max-width: 960px) {
  .city-weather-grid {
    grid-template-columns: 1fr;
  }

  .city-weather-now {
    align-items: flex-start;
  }
}

@media (max-width: 720px) {
  .city-weather-panel,
  .city-map-panel {
    padding: 16px;
    border-radius: 20px;
  }

  .city-weather-now {
    flex-direction: column;
  }

  .city-map-link {
    width: 100%;
  }

  .city-static-map-frame {
    min-height: 180px;
  }
}
</style>
