<template>
  <article class="card section-shell">
    <div class="title-row">
      <SectionHeader
        eyebrow="Province"
        title="省域旅行灵感"
        description="调用高德行政区与地理编码接口，先看中国总图，再点进省份查看具体城市分布。"
      />
      <div class="action-row">
        <button v-if="selectedProvinceName" class="btn btn-secondary" type="button" @click="backToOverview">返回中国地图</button>
        <RouterLink
          class="btn btn-secondary"
          :to="selectedProvinceName ? { name: 'cities', query: { province: selectedProvinceName } } : { name: 'cities' }"
        >
          {{ selectedProvinceName ? '查看全省城市' : '全部城市' }}
        </RouterLink>
      </div>
    </div>

    <div v-if="overviewLoading && !overview" class="page-state" style="margin-top: 24px">
      <strong>正在加载中国旅行地图...</strong>
    </div>

    <div v-else-if="showFallback" class="grid" style="margin-top: 24px">
      <div class="timeline-item province-map-alert">
        <strong>{{ mapErrorTitle }}</strong>
        <p class="muted">{{ mapErrorMessage }}</p>
      </div>

      <div class="province-showcase-grid">
        <button
          v-for="province in fallbackProvinces"
          :key="province.province"
          class="province-showcase-card"
          type="button"
          @click="goToProvinceList(province.province)"
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
              主入口城市：{{ province.topCity?.name || '待补充' }}，{{ province.attractionCount }} 景点
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
        </button>
      </div>
    </div>

    <div v-else class="map-explorer-shell province-map-shell" style="margin-top: 24px">
      <section class="map-explorer-board province-inspiration-board">
        <div class="province-map-toolbar">
          <div>
            <span class="eyebrow">{{ selectedProvinceName ? 'Province Map' : 'China Map' }}</span>
            <strong>{{ selectedProvinceName || overview?.country?.name || '中国' }}</strong>
          </div>
          <p class="muted province-map-hint">
            {{ selectedProvinceName ? '点击城市点位可直接进入城市详情。' : '点击地图点位可进入对应省份地图。' }}
          </p>
        </div>

        <div v-if="provinceLoading" class="province-map-loading">正在加载省份地图...</div>

        <div class="province-map-stage">
          <svg v-if="projectedMap.paths.length" class="province-map-svg" :viewBox="`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`" preserveAspectRatio="xMidYMid meet">
            <g class="province-map-path-layer">
              <path
                v-for="(path, index) in projectedMap.paths"
                :key="`${selectedProvinceName || 'china'}-${index}`"
                class="province-map-path"
                :d="path"
              />
            </g>
          </svg>

          <div v-else class="province-map-empty muted">暂无可展示的行政区边界数据。</div>

          <button
            v-for="marker in projectedMap.markers"
            :key="selectedProvinceName ? `city-${marker.id}` : `province-${marker.province}`"
            class="province-map-node"
            :class="{ active: selectedProvinceName ? false : marker.province === hoveredProvince }"
            :style="{ left: `${marker.xPct}%`, top: `${marker.yPct}%` }"
            type="button"
            @mouseenter="hoveredProvince = marker.province || ''"
            @mouseleave="hoveredProvince = ''"
            @click="handleMarkerClick(marker)"
          >
            <strong>{{ selectedProvinceName ? marker.name : marker.top_city?.name || marker.short_name }}</strong>
            <span>{{ selectedProvinceName ? `${marker.attraction_count || 0} 景点` : marker.short_name }}</span>
            <small>
              {{ selectedProvinceName ? `建议 ${marker.recommended_days || 2} 天` : `${marker.city_count} 城市` }}
            </small>
          </button>
        </div>
      </section>

      <aside class="map-explorer-sidebar province-map-sidebar">
        <template v-if="selectedProvince">
          <div class="timeline-item province-map-summary-card">
            <span class="eyebrow">{{ selectedProvince.short_name }}</span>
            <strong>{{ selectedProvince.name }}</strong>
            <p class="muted">
              共收录 {{ selectedProvince.city_count }} 座城市，{{ selectedProvince.attraction_count }} 个景点。
            </p>
            <div class="chip-row">
              <span v-if="selectedProvince.average_rating" class="pill">评分 {{ selectedProvince.average_rating }}</span>
              <span v-if="selectedProvince.top_city?.name" class="pill">主入口 {{ selectedProvince.top_city.name }}</span>
            </div>
          </div>

          <button
            v-for="city in provinceCities"
            :key="city.id"
            class="timeline-item province-map-list-card"
            type="button"
            @click="goToCity(city.id)"
          >
            <div class="title-row compact-row">
              <strong>{{ city.name }}</strong>
              <span class="pill">{{ city.attraction_count || 0 }} 景点</span>
            </div>
            <p class="muted province-map-city-intro">{{ city.short_intro || '查看该城市的景点与旅行建议。' }}</p>
            <div class="chip-row">
              <span v-if="city.average_rating" class="pill">评分 {{ city.average_rating }}</span>
              <span v-for="tag in (city.tags || []).slice(0, 2)" :key="`${city.id}-${tag}`" class="tag-pill">{{ tag }}</span>
            </div>
          </button>
        </template>

        <template v-else>
          <div class="timeline-item province-map-summary-card">
            <span class="eyebrow">AMap</span>
            <strong>全国省域入口</strong>
            <p class="muted">每个点位使用该省主入口城市作为标记，点击后查看该省的城市分布地图。</p>
          </div>

          <button
            v-for="province in overviewProvinces.slice(0, 12)"
            :key="province.province"
            class="timeline-item province-map-list-card"
            type="button"
            @click="openProvince(province.province)"
          >
            <div class="title-row compact-row">
              <strong>{{ province.short_name }}</strong>
              <span class="pill">{{ province.city_count }} 城市</span>
            </div>
            <p class="muted province-map-city-intro">
              主入口城市：{{ province.top_city?.name || '待补充' }}，{{ province.attraction_count }} 景点
            </p>
            <div class="chip-row">
              <span v-if="province.average_rating" class="pill">评分 {{ province.average_rating }}</span>
              <span v-for="tag in (province.top_city?.tags || []).slice(0, 2)" :key="`${province.province}-${tag}`" class="tag-pill">{{ tag }}</span>
            </div>
          </button>
        </template>
      </aside>
    </div>
  </article>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import SectionHeader from "../SectionHeader.vue";
import { getProvinceMapDetail, getProvinceMapOverview } from "../../services/api";

const VIEWBOX_WIDTH = 1000;
const VIEWBOX_HEIGHT = 720;
const VIEWBOX_PADDING = 42;

const props = defineProps({
  provinces: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const router = useRouter();
const overviewLoading = ref(true);
const provinceLoading = ref(false);
const mapErrorMessage = ref("");
const overview = ref(null);
const selectedProvinceName = ref("");
const selectedProvinceDetail = ref(null);
const hoveredProvince = ref("");
const provinceCache = new Map();

const fallbackProvinces = computed(() => props.provinces.slice(0, 8));
const overviewProvinces = computed(() => overview.value?.provinces || []);
const selectedProvince = computed(() => selectedProvinceDetail.value?.province || null);
const provinceCities = computed(() => selectedProvinceDetail.value?.cities || []);
const activeBoundary = computed(() =>
  selectedProvinceName.value ? selectedProvince.value?.boundary || [] : overview.value?.country?.boundary || [],
);
const activeMarkers = computed(() => (selectedProvinceName.value ? provinceCities.value : overviewProvinces.value));
const showFallback = computed(() => !overviewLoading.value && (!overview.value || !!mapErrorMessage.value));
const mapErrorTitle = computed(() => (mapErrorMessage.value ? "高德地图暂不可用" : "正在准备地图数据"));

function provinceCoverStyle(province) {
  const image = province.topCity?.cover_image;
  return {
    background: image
      ? `linear-gradient(180deg, rgba(10, 37, 46, 0.14), rgba(10, 37, 46, 0.72)), url(${image}) center/cover`
      : "linear-gradient(135deg, #0d5c63, #1b4965 58%, #f28f3b)",
  };
}

function goToProvinceList(province) {
  router.push({ name: "cities", query: { province } });
}

function goToCity(id) {
  router.push({ name: "city-detail", params: { id } });
}

function backToOverview() {
  selectedProvinceName.value = "";
  selectedProvinceDetail.value = null;
  hoveredProvince.value = "";
}

async function loadOverview() {
  overviewLoading.value = true;
  mapErrorMessage.value = "";
  try {
    overview.value = await getProvinceMapOverview();
  } catch (error) {
    mapErrorMessage.value = error.response?.data?.detail || "高德行政区接口未配置或暂时不可用，已降级为原省份入口卡片。";
  } finally {
    overviewLoading.value = false;
  }
}

async function openProvince(province) {
  if (!province) return;
  selectedProvinceName.value = province;
  hoveredProvince.value = province;
  if (provinceCache.has(province)) {
    selectedProvinceDetail.value = provinceCache.get(province);
    return;
  }

  provinceLoading.value = true;
  try {
    const data = await getProvinceMapDetail(province);
    provinceCache.set(province, data);
    if (selectedProvinceName.value === province) {
      selectedProvinceDetail.value = data;
    }
  } catch (error) {
    mapErrorMessage.value = error.response?.data?.detail || `${province} 地图暂时不可用。`;
    selectedProvinceName.value = "";
    selectedProvinceDetail.value = null;
  } finally {
    provinceLoading.value = false;
  }
}

function handleMarkerClick(marker) {
  if (selectedProvinceName.value) {
    goToCity(marker.id);
    return;
  }
  openProvince(marker.province);
}

function buildProjectedMap(polygons, markers) {
  const normalizedPolygons = (polygons || [])
    .map((polygon) =>
      (polygon || [])
        .map((point) => ({
          longitude: Number(point.longitude),
          latitude: Number(point.latitude),
        }))
        .filter((point) => Number.isFinite(point.longitude) && Number.isFinite(point.latitude)),
    )
    .filter((polygon) => polygon.length >= 3);

  const normalizedMarkers = (markers || [])
    .map((marker) => ({
      ...marker,
      longitude: Number(marker.longitude),
      latitude: Number(marker.latitude),
    }))
    .filter((marker) => Number.isFinite(marker.longitude) && Number.isFinite(marker.latitude));

  const allPoints = normalizedPolygons.flat().concat(normalizedMarkers);
  if (!allPoints.length) {
    return { paths: [], markers: [] };
  }

  const longitudes = allPoints.map((point) => point.longitude);
  const latitudes = allPoints.map((point) => point.latitude);
  const minLng = Math.min(...longitudes);
  const maxLng = Math.max(...longitudes);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const spanLng = Math.max(maxLng - minLng, 1);
  const spanLat = Math.max(maxLat - minLat, 1);
  const innerWidth = VIEWBOX_WIDTH - VIEWBOX_PADDING * 2;
  const innerHeight = VIEWBOX_HEIGHT - VIEWBOX_PADDING * 2;
  const scale = Math.min(innerWidth / spanLng, innerHeight / spanLat);
  const actualWidth = spanLng * scale;
  const actualHeight = spanLat * scale;
  const offsetX = (VIEWBOX_WIDTH - actualWidth) / 2;
  const offsetY = (VIEWBOX_HEIGHT - actualHeight) / 2;

  function projectPoint(point) {
    const x = offsetX + (point.longitude - minLng) * scale;
    const y = offsetY + (maxLat - point.latitude) * scale;
    return {
      x,
      y,
      xPct: Number(((x / VIEWBOX_WIDTH) * 100).toFixed(3)),
      yPct: Number(((y / VIEWBOX_HEIGHT) * 100).toFixed(3)),
    };
  }

  return {
    paths: normalizedPolygons.map((polygon) => {
      const commands = polygon.map((point, index) => {
        const projected = projectPoint(point);
        return `${index === 0 ? "M" : "L"} ${projected.x.toFixed(2)} ${projected.y.toFixed(2)}`;
      });
      return `${commands.join(" ")} Z`;
    }),
    markers: normalizedMarkers.map((marker) => ({
      ...marker,
      ...projectPoint(marker),
    })),
  };
}

const projectedMap = computed(() => buildProjectedMap(activeBoundary.value, activeMarkers.value));

onMounted(loadOverview);
</script>

<style scoped>
.province-map-shell {
  align-items: start;
}

.province-inspiration-board {
  display: grid;
  gap: 18px;
  padding: 22px;
}

.province-map-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.province-map-toolbar strong {
  display: block;
  margin-top: 8px;
  color: var(--secondary);
  font-size: 22px;
}

.province-map-hint {
  max-width: 280px;
  margin: 0;
  text-align: right;
}

.province-map-stage {
  position: relative;
  min-height: 640px;
  overflow: hidden;
  border-radius: 30px;
  border: 1px solid rgba(17, 57, 68, 0.08);
  background:
    radial-gradient(circle at 20% 16%, rgba(223, 127, 50, 0.18), transparent 20%),
    radial-gradient(circle at 78% 14%, rgba(22, 114, 124, 0.18), transparent 18%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(236, 245, 246, 0.92));
}

.province-map-stage::before {
  content: "";
  position: absolute;
  inset: 24px;
  border-radius: 26px;
  border: 1px dashed rgba(10, 94, 99, 0.12);
  pointer-events: none;
}

.province-map-svg {
  width: 100%;
  height: 100%;
  min-height: 640px;
}

.province-map-path {
  fill: rgba(10, 94, 99, 0.12);
  stroke: rgba(10, 94, 99, 0.4);
  stroke-width: 1.6;
  stroke-linejoin: round;
}

.province-map-node {
  position: absolute;
  z-index: 2;
  display: grid;
  gap: 4px;
  min-width: 110px;
  max-width: 170px;
  padding: 12px 14px;
  border: 0;
  border-radius: 20px;
  color: var(--secondary);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 14px 28px rgba(11, 46, 54, 0.12);
  cursor: pointer;
  text-align: left;
  transform: translate(-50%, -50%);
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.province-map-node:hover,
.province-map-node.active {
  transform: translate(-50%, -52%);
  color: white;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 22px 38px rgba(11, 46, 54, 0.18);
}

.province-map-node span,
.province-map-node small {
  color: inherit;
  opacity: 0.82;
}

.province-map-sidebar {
  gap: 14px;
}

.province-map-summary-card {
  display: grid;
  gap: 10px;
}

.province-map-summary-card strong,
.province-map-list-card strong {
  color: var(--secondary);
}

.province-map-list-card {
  width: 100%;
  border: 0;
  cursor: pointer;
  text-align: left;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.province-map-list-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 36px rgba(10, 68, 73, 0.1);
}

.province-map-city-intro {
  margin: 10px 0 0;
}

.province-map-alert {
  display: grid;
  gap: 8px;
}

.province-map-alert p {
  margin: 0;
}

.province-map-loading,
.province-map-empty {
  display: grid;
  place-items: center;
  min-height: 92px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.66);
}

@media (max-width: 720px) {
  .province-map-toolbar,
  .province-map-hint {
    text-align: left;
  }

  .province-map-stage,
  .province-map-svg {
    min-height: 520px;
  }

  .province-map-node {
    min-width: 96px;
    max-width: 128px;
    padding: 10px 12px;
  }
}
</style>
