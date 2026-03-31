<template>
  <section class="page planner-page">
    <div class="planner-shell">
      <article class="card planner-control-panel">
        <div class="planner-hero-card">
          <h1>AI 旅行规划</h1>
        </div>

        <form class="planner-form" @submit.prevent="handleSubmit">
          <section class="planner-form-section">
            <div class="planner-section-head">
              <span>城市锚点</span>
              <strong>先确定这次从哪出发，要去哪里</strong>
            </div>

            <div class="field-grid planner-field-grid">
              <div class="field planner-search-field">
                <label for="targetCity">目标城市</label>
                <div class="planner-search-box">
                  <input
                    id="targetCity"
                    v-model.trim="targetKeyword"
                    autocomplete="off"
                    placeholder="搜索并选择目的地"
                    @focus="targetMenuOpen = true"
                    @blur="closeMenuLater('target')"
                  />
                  <div v-if="targetMenuOpen && filteredTargetCities.length" class="planner-search-panel">
                    <button
                      v-for="city in filteredTargetCities"
                      :key="city.id"
                      class="planner-search-option"
                      type="button"
                      @mousedown.prevent="selectTargetCity(city)"
                    >
                      <div>
                        <strong>{{ city.name }}</strong>
                        <span>{{ city.province || "中国" }}</span>
                      </div>
                      <small>{{ city.attraction_count || 0 }} 个景点</small>
                    </button>
                  </div>
                </div>
              </div>

              <div class="field planner-search-field">
                <label for="departureCity">出发城市</label>
                <div class="planner-search-box">
                  <input
                    id="departureCity"
                    v-model.trim="departureKeyword"
                    autocomplete="off"
                    placeholder="搜索你的出发地"
                    @focus="departureMenuOpen = true"
                    @blur="closeMenuLater('departure')"
                  />
                  <div v-if="departureMenuOpen && filteredDepartureCities.length" class="planner-search-panel">
                    <button
                      v-for="city in filteredDepartureCities"
                      :key="city.id"
                      class="planner-search-option"
                      type="button"
                      @mousedown.prevent="selectDepartureCity(city)"
                    >
                      <div>
                        <strong>{{ city.name }}</strong>
                        <span>{{ city.province || "中国" }}</span>
                      </div>
                      <small>{{ city.attraction_count || 0 }} 个景点</small>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section class="planner-form-section">
            <div class="planner-section-head">
              <span>行程参数</span>
              <strong>决定预算、节奏和同行方式</strong>
            </div>

            <div class="field-grid planner-field-grid">
              <div class="field">
                <label for="durationDays">出行天数</label>
                <select id="durationDays" v-model="form.duration_days">
                  <option v-for="value in [2, 3, 4, 5, 6]" :key="value" :value="value">{{ value }} 天</option>
                </select>
              </div>

              <div class="field">
                <label for="seasonHint">季节</label>
                <select id="seasonHint" v-model="form.season_hint">
                  <option value="">不限</option>
                  <option value="春">春季</option>
                  <option value="夏">夏季</option>
                  <option value="秋">秋季</option>
                  <option value="冬">冬季</option>
                </select>
              </div>

              <div class="field">
                <label for="budgetLevel">预算</label>
                <select id="budgetLevel" v-model="form.budget_level">
                  <option value="value">经济型</option>
                  <option value="balanced">均衡型</option>
                  <option value="premium">品质型</option>
                </select>
              </div>

              <div class="field">
                <label for="companions">同行方式</label>
                <select id="companions" v-model="form.companions">
                  <option value="双人">双人</option>
                  <option value="亲子">亲子</option>
                  <option value="朋友结伴">朋友结伴</option>
                  <option value="家庭">家庭</option>
                </select>
              </div>
            </div>
          </section>

          <section class="planner-form-section">
            <div class="planner-section-head">
              <span>兴趣偏好</span>
              <strong>告诉系统你更想玩什么</strong>
            </div>

            <div class="planner-interest-grid">
              <button
                v-for="interest in interestOptions"
                :key="interest"
                class="planner-interest-chip"
                :class="{ active: form.interests.includes(interest) }"
                type="button"
                @click="toggleInterest(interest)"
              >
                {{ interest }}
              </button>
            </div>
          </section>

          <section class="planner-form-section">
            <div class="planner-section-head">
              <span>生成方式</span>
              <strong>选择千问直连，或使用数据库 Agent 规划</strong>
            </div>

            <div class="planner-mode-select-grid">
              <button
                v-for="item in planningModes"
                :key="item.value"
                class="planner-mode-card"
                :class="{ active: form.mode === item.value }"
                type="button"
                @click="form.mode = item.value"
              >
                <strong>{{ item.label }}</strong>
                <p>{{ item.description }}</p>
              </button>
            </div>
          </section>

          <section class="planner-form-section planner-form-footer">
            <p class="planner-subtle-note">目标城市、出发城市和兴趣越明确，生成结果越稳定。</p>

            <p v-if="errorMessage" class="planner-error-banner">{{ errorMessage }}</p>

            <div class="planner-submit-row">
              <button class="btn btn-primary planner-submit-button" type="submit" :disabled="submitDisabled">
                {{ loading ? "正在生成行程..." : "生成 AI 行程" }}
              </button>
              <button class="btn btn-secondary" type="button" @click="resetForm">重置参数</button>
            </div>
          </section>
        </form>

        <section class="planner-form-section planner-history-section">
          <div class="planner-section-head planner-history-head">
            <div>
              <span>历史行程</span>
              <strong>已保存的 AI 规划</strong>
            </div>
            <button
              v-if="authState.user && savedPlans.length > collapsedPlanCount"
              class="btn btn-secondary planner-history-toggle"
              type="button"
              @click="plansExpanded = !plansExpanded"
            >
              {{ plansExpanded ? "收起" : `展开全部 (${savedPlans.length})` }}
            </button>
          </div>

          <div v-if="authState.user" class="planner-history-stack">
            <p v-if="historyMessage" class="planner-subtle-note">{{ historyMessage }}</p>

            <div v-if="loadingPlans" class="planner-history-empty">
              <p class="muted">正在读取历史行程...</p>
            </div>

            <div v-else-if="visibleSavedPlans.length" class="planner-history-list">
              <button
                v-for="plan in visibleSavedPlans"
                :key="plan.id"
                class="planner-history-card"
                :class="{ active: activePlanId === plan.id }"
                type="button"
                @click="restoreSavedPlan(plan)"
              >
                <div class="planner-history-copy">
                  <strong>{{ plan.title }}</strong>
                  <p class="muted">{{ plan.city_detail?.name || "未关联城市" }} | {{ plan.duration_days }} 天</p>
                  <p class="muted">{{ formatPlanDate(plan.created_at) }}</p>
                </div>
                <span class="pill">RMB {{ plan.estimated_budget || 0 }}</span>
              </button>
              <p v-if="!plansExpanded && hiddenPlanCount > 0" class="muted planner-history-more">
                还有 {{ hiddenPlanCount }} 条已保存行程，点击“展开全部”查看。
              </p>
            </div>

            <div v-else class="planner-history-empty">
              <p class="muted">还没有已保存的 AI 行程，生成后会自动出现在这里。</p>
            </div>
          </div>

          <div v-else class="planner-history-empty">
            <p class="muted">登录后会自动保存 AI 行程，并在这里显示历史记录。</p>
          </div>
        </section>
      </article>

      <article class="card planner-result-panel">
        <div class="planner-result-header">
          <div>
            <p class="planner-eyebrow">Result Console</p>
            <h2>生成结果</h2>
            <p class="muted">预算、必去点位与逐日动线会优先展示，推荐城市放在结果底部作为备选。</p>
          </div>
          <div v-if="result" class="planner-mode-badges">
            <span class="pill">{{ plannerStrategyLabel }}</span>
            <span class="pill">{{ plannerModeLabel }}</span>
            <span class="pill" v-if="result.planner_model">{{ result.planner_model }}</span>
          </div>
        </div>

        <div v-if="loading" class="planner-loading-stage">
          <section class="planner-loading-hero">
            <div class="planner-loading-orbit" aria-hidden="true">
              <span class="planner-loading-ring planner-loading-ring-a"></span>
              <span class="planner-loading-ring planner-loading-ring-b"></span>
              <span class="planner-loading-ring planner-loading-ring-c"></span>
              <span class="planner-loading-core"></span>
            </div>
            <div class="planner-loading-copy">
              <p class="planner-eyebrow">In Progress</p>
              <h3>AI 正在生成行程</h3>
              <p>{{ loadingStep.description }}</p>
            </div>
          </section>

          <section class="planner-loading-step-grid">
            <article
              v-for="(step, index) in loadingSteps"
              :key="step.title"
              class="planner-loading-step"
              :class="{
                active: index === loadingStepIndex,
                passed: index < loadingStepIndex,
              }"
            >
              <span>{{ step.title }}</span>
              <p>{{ step.detail }}</p>
            </article>
          </section>
        </div>

        <div v-else-if="result" class="planner-result-stack">
          <section class="planner-summary-hero">
            <div class="planner-summary-copy">
              <p class="planner-eyebrow">Plan Blueprint</p>
              <h3>{{ result.trip_title }}</h3>
              <p>{{ result.summary }}</p>
            </div>
            <div class="planner-summary-meta">
              <div class="planner-summary-pill">
                <span>预算</span>
                <strong>RMB {{ result.estimated_budget }}</strong>
              </div>
              <div class="planner-summary-pill">
                <span>方案</span>
                <strong>{{ plannerStrategyLabel }}</strong>
              </div>
              <div class="planner-summary-pill">
                <span>引擎</span>
                <strong>{{ plannerModeLabel }}</strong>
              </div>
              <div class="planner-summary-pill" v-if="result.matched_city_name">
                <span>匹配城市</span>
                <strong>{{ result.matched_city_name }}</strong>
              </div>
            </div>
          </section>

          <p v-if="result.fallback_reason" class="planner-warning-banner">
            {{ result.fallback_reason }}
          </p>

          <section v-if="result.city" class="planner-city-hero">
            <div class="planner-city-cover" :style="cityCoverStyle(result.city.cover_image)"></div>
            <div class="planner-city-copy">
              <p class="planner-eyebrow">Target City</p>
              <h3>{{ result.city.name }}</h3>
              <p class="muted">
                {{ result.city.province || "中国" }} | {{ result.city.recommended_days || form.duration_days }} 天建议游玩 |
                {{ result.city.attraction_count || 0 }} 个景点
              </p>
              <div class="planner-tag-row">
                <span v-for="tag in (result.city.tags || []).slice(0, 5)" :key="tag" class="pill">{{ tag }}</span>
              </div>
            </div>
          </section>

          <section class="planner-stat-grid">
            <div class="planner-stat-card">
              <span>行程天数</span>
              <strong>{{ result.itinerary.length }}</strong>
              <p>按天拆分的可执行日程</p>
            </div>
            <div class="planner-stat-card">
              <span>必去景点</span>
              <strong>{{ result.must_visit_spots.length }}</strong>
              <p>系统优先保留的核心目的地</p>
            </div>
            <div class="planner-stat-card">
              <span>推荐备选</span>
              <strong>{{ result.recommended_cities.length }}</strong>
              <p>相近主题或同省的备选城市</p>
            </div>
            <div class="planner-stat-card">
              <span>打包清单</span>
              <strong>{{ result.packing_list.length }}</strong>
              <p>出发前建议准备的关键物品</p>
            </div>
          </section>

          <section class="planner-bento-grid">
            <div class="planner-bento-card">
              <div class="planner-card-head">
                <strong>预算拆分</strong>
                <span class="muted">Estimated Breakdown</span>
              </div>
              <div class="budget-list">
                <div v-for="(value, key) in result.budget_breakdown" :key="key" class="budget-item">
                  <span>{{ budgetLabels[key] || key }}</span>
                  <strong>RMB {{ value }}</strong>
                </div>
              </div>
            </div>

            <div class="planner-bento-card">
              <div class="planner-card-head">
                <strong>必去景点</strong>
                <span class="muted">Must Visit</span>
              </div>
              <div class="planner-spot-grid">
                <RouterLink
                  v-for="spot in result.must_visit_spots"
                  :key="spot.id"
                  class="planner-spot-card"
                  :to="`/attractions/${spot.id}`"
                >
                  <strong>{{ spot.name }}</strong>
                  <p>{{ spot.ticket_info || spot.address || "查看景点详情" }}</p>
                </RouterLink>
              </div>
            </div>
          </section>

          <section v-if="result.packing_list.length" class="planner-bento-card">
            <div class="planner-card-head">
              <strong>打包清单</strong>
              <span class="muted">Packing List</span>
            </div>
            <div class="planner-tag-row">
              <span v-for="item in result.packing_list" :key="item" class="pill">{{ item }}</span>
            </div>
          </section>

          <section class="planner-itinerary-stack">
            <div class="planner-card-head">
              <strong>逐日行程</strong>
              <span class="muted">Daily Timeline</span>
            </div>

            <article v-for="day in result.itinerary" :key="day.day" class="planner-day-card">
              <div class="planner-day-head">
                <div>
                  <p class="planner-day-kicker">Day {{ day.day }}</p>
                  <h3>{{ day.theme }}</h3>
                  <p class="muted">{{ day.summary }}</p>
                </div>
                <span class="pill">{{ day.blocks.length }} 个时段</span>
              </div>

              <div class="planner-block-grid">
                <div v-for="block in day.blocks" :key="`${day.day}-${block.period}`" class="planner-block-card">
                  <div class="planner-block-top">
                    <span class="pill planner-period-pill">{{ block.period }}</span>
                    <span class="planner-block-time">{{ block.spot.suggested_play_time || "灵活安排" }}</span>
                  </div>
                  <RouterLink class="planner-spot-link" :to="`/attractions/${block.spot.id}`">
                    {{ block.spot.name }}
                  </RouterLink>
                  <p>{{ block.summary }}</p>
                  <div class="planner-block-meta">
                    <span>{{ block.spot.opening_hours || "开放时间以现场为准" }}</span>
                    <span>{{ block.spot.ticket_info || "门票以现场为准" }}</span>
                  </div>
                </div>
              </div>

              <div class="planner-day-footer">
                <p><strong>动线建议：</strong>{{ day.transport_tip }}</p>
                <div class="planner-tag-row">
                  <span v-for="item in day.checklist" :key="item" class="pill">{{ item }}</span>
                </div>
              </div>
            </article>
          </section>

          <section v-if="result.recommended_cities.length" class="planner-recommendation-zone">
            <div class="planner-card-head">
              <strong>推荐备选城市</strong>
              <span class="muted">Alternative Cities</span>
            </div>
            <div class="grid grid-2 planner-city-grid">
              <CityCard v-for="city in result.recommended_cities" :key="city.id" :city="city" />
            </div>
          </section>
        </div>

        <div v-else class="planner-empty-state">
          <p class="planner-eyebrow">Awaiting Input</p>
          <h3>右侧结果区已就绪</h3>
          <p>填写左侧参数后，系统会先锁定目标城市，再生成预算与逐日路线。</p>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import CityCard from "../components/CityCard.vue";
import { generatePlan, getCities, getTravelPlans } from "../services/api";
import { authState } from "../stores/auth";

const route = useRoute();
const PLANNER_CACHE_KEY = "smart_journey_planner_state";
const collapsedPlanCount = 3;
const loading = ref(false);
const result = ref(null);
const errorMessage = ref("");
const cityOptions = ref([]);
const savedPlans = ref([]);
const loadingPlans = ref(false);
const historyMessage = ref("");
const activePlanId = ref(null);
const plansExpanded = ref(false);
const targetKeyword = ref(typeof route.query.targetCity === "string" ? route.query.targetCity : "");
const departureKeyword = ref("");
const targetMenuOpen = ref(false);
const departureMenuOpen = ref(false);
const loadingStepIndex = ref(0);

const defaultInterests = ["自然风光", "美食"];
const interestOptions = ["自然风光", "人文古迹", "亲子休闲", "户外徒步", "摄影出片", "美食"];
const planningModes = [
  {
    value: "agent",
    label: "数据库 Agent",
    description: "优先依据站内城市和景点库规划，约束更强，结果更贴近系统数据。",
  },
  {
    value: "qwen",
    label: "千问直连",
    description: "直接走千问通用规划能力，表达更开放，但会更依赖模型生成。",
  },
];
const budgetLabels = {
  transport: "交通",
  tickets: "门票",
  food: "餐饮",
  stay: "住宿",
};
const loadingSteps = [
  {
    title: "锁定城市",
    detail: "根据目标城市、预算与季节约束缩小候选范围。",
    description: "正在比对城市库与景点池，先确定本次行程的主场景。",
  },
  {
    title: "筛选景点",
    detail: "结合兴趣偏好挑出更值得进入行程的点位。",
    description: "正在为你筛掉噪声景点，保留更贴合偏好的候选内容。",
  },
  {
    title: "编排行程",
    detail: "按天数与节奏生成逐日动线和时段安排。",
    description: "正在组织每天的主题、顺序与建议玩法，确保路线可执行。",
  },
  {
    title: "整理结果",
    detail: "汇总预算、打包清单和备选城市。",
    description: "正在整理最终展示内容，很快就能看到完整结果。",
  },
];

function createBudgetBreakdown(totalBudget) {
  const total = Number(totalBudget || 0);
  if (!total) return {};
  return {
    transport: Math.floor(total * 0.28),
    tickets: Math.floor(total * 0.22),
    food: Math.floor(total * 0.2),
    stay: Math.max(0, total - Math.floor(total * 0.28) - Math.floor(total * 0.22) - Math.floor(total * 0.2)),
  };
}

function collectPlanSpots(itinerary = []) {
  const seen = new Set();
  const spots = [];

  itinerary.forEach((day) => {
    const candidates = Array.isArray(day?.spots) && day.spots.length
      ? day.spots
      : (day?.blocks || []).map((block) => block?.spot).filter(Boolean);

    candidates.forEach((spot) => {
      if (!spot?.id || seen.has(spot.id)) return;
      seen.add(spot.id);
      spots.push(spot);
    });
  });

  return spots;
}

function normalizePlannerResult(payload = {}) {
  const itinerary = Array.isArray(payload.itinerary) ? payload.itinerary : [];
  return {
    trip_title: payload.trip_title || payload.title || "",
    summary: payload.summary || "",
    estimated_budget: Number(payload.estimated_budget || 0),
    budget_breakdown: payload.budget_breakdown || createBudgetBreakdown(payload.estimated_budget),
    city: payload.city || payload.city_detail || null,
    recommended_cities: Array.isArray(payload.recommended_cities) ? payload.recommended_cities : [],
    must_visit_spots: Array.isArray(payload.must_visit_spots) && payload.must_visit_spots.length
      ? payload.must_visit_spots
      : collectPlanSpots(itinerary).slice(0, 3),
    packing_list: Array.isArray(payload.packing_list) ? payload.packing_list : [],
    itinerary,
    planner_mode: payload.planner_mode || "saved_plan",
    planner_strategy: payload.planner_strategy || "saved",
    planner_provider: payload.planner_provider || "saved",
    planner_model: payload.planner_model || "",
    matched_city_name: payload.matched_city_name || payload.city?.name || payload.city_detail?.name || "",
    failure_reason: payload.failure_reason || "",
    failure_stage: payload.failure_stage || "",
    fallback_reason: payload.fallback_reason || "",
    used_fallback: Boolean(payload.used_fallback),
    saved_plan: payload.saved_plan || null,
  };
}

function buildPlannerRequestFromSavedPlan(plan) {
  return {
    target_city: plan?.city_detail?.name || "",
    departure_city: plan?.departure_city || "",
    duration_days: Number(plan?.duration_days || 3),
    season_hint: "",
    budget_level: plan?.budget_level || "balanced",
    companions: plan?.companions || "朋友结伴",
    interests: Array.isArray(plan?.interests) && plan.interests.length ? [...plan.interests] : [...defaultInterests],
    mode: "agent",
  };
}

function buildRouteContext(query = route.query) {
  return {
    targetCity: typeof query?.targetCity === "string" ? query.targetCity : "",
    cityId: query?.cityId ? String(query.cityId) : "",
  };
}

function applyRequestPayload(payload = {}) {
  form.target_city = payload.target_city || "";
  form.departure_city = payload.departure_city || getDefaultDepartureCity();
  form.duration_days = Number(payload.duration_days || 3);
  form.season_hint = payload.season_hint || "";
  form.budget_level = payload.budget_level || "balanced";
  form.companions = payload.companions || "朋友结伴";
  form.interests = Array.isArray(payload.interests) && payload.interests.length ? [...payload.interests] : [...defaultInterests];
  form.mode = payload.mode === "qwen" ? "qwen" : "agent";
  targetKeyword.value = form.target_city;
  departureKeyword.value = form.departure_city;
}

function persistPlannerState(requestPayload, resultPayload) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(
    PLANNER_CACHE_KEY,
    JSON.stringify({
      requestPayload,
      resultPayload,
      activePlanId: activePlanId.value,
      routeContext: buildRouteContext(),
    }),
  );
}

function clearPlannerState() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(PLANNER_CACHE_KEY);
}

function restorePlannerState() {
  if (typeof window === "undefined") return false;
  const raw = window.sessionStorage.getItem(PLANNER_CACHE_KEY);
  if (!raw) return false;

  try {
    const parsed = JSON.parse(raw);
    const currentRouteContext = buildRouteContext();
    const hasExplicitRouteContext = Boolean(currentRouteContext.targetCity || currentRouteContext.cityId);
    if (hasExplicitRouteContext) {
      if (!parsed?.routeContext) {
        return false;
      }
      const sameRouteContext =
        parsed.routeContext.targetCity === currentRouteContext.targetCity &&
        parsed.routeContext.cityId === currentRouteContext.cityId;
      if (!sameRouteContext) {
        return false;
      }
    }
    if (parsed?.requestPayload) {
      applyRequestPayload(parsed.requestPayload);
    }
    if (parsed?.resultPayload) {
      result.value = normalizePlannerResult(parsed.resultPayload);
    }
    activePlanId.value = parsed?.activePlanId || parsed?.resultPayload?.saved_plan?.id || null;
    plansExpanded.value = false;
    return Boolean(parsed?.resultPayload);
  } catch {
    clearPlannerState();
    return false;
  }
}

function getDefaultDepartureCity() {
  return cityOptions.value[0]?.name || "";
}

const defaultFormState = () => ({
  target_city: typeof route.query.targetCity === "string" ? route.query.targetCity : "",
  departure_city: getDefaultDepartureCity(),
  duration_days: 3,
  season_hint: "",
  budget_level: "balanced",
  companions: "朋友结伴",
  interests: [...defaultInterests],
  mode: "agent",
});

const form = reactive(defaultFormState());

const submitDisabled = computed(() => loading.value || !targetKeyword.value.trim() || !departureKeyword.value.trim());
const loadingStep = computed(() => loadingSteps[loadingStepIndex.value] || loadingSteps[0]);
const plannerStrategyLabel = computed(() => {
  if (!result.value) {
    return form.mode === "qwen" ? "千问直连" : "数据库 Agent";
  }
  if (result.value.planner_mode === "saved_plan") {
    return "历史记录";
  }
  return result.value.planner_strategy === "qwen" ? "千问直连" : "数据库 Agent";
});
const plannerModeLabel = computed(() => {
  if (!result.value) return "";
  if (result.value.planner_mode === "saved_plan") {
    return "已保存行程";
  }
  if (result.value.used_fallback) {
    return "规则兜底";
  }
  if (result.value.planner_mode === "database_agent") {
    return "数据库 Agent 执行";
  }
  if (result.value.planner_mode === "qwen_direct") {
    return "千问直连执行";
  }
  if (result.value.planner_provider === "qwen") {
    return "千问生成";
  }
  if (result.value.planner_mode === "failed") {
    return "生成失败";
  }
  return "规则规划";
});
const hiddenPlanCount = computed(() => Math.max(0, savedPlans.value.length - collapsedPlanCount));
const visibleSavedPlans = computed(() => {
  if (plansExpanded.value || savedPlans.value.length <= collapsedPlanCount) {
    return savedPlans.value;
  }

  const activeIndex = savedPlans.value.findIndex((item) => item.id === activePlanId.value);
  if (activeIndex >= collapsedPlanCount) {
    return [
      ...savedPlans.value.slice(0, Math.max(0, collapsedPlanCount - 1)),
      savedPlans.value[activeIndex],
    ];
  }

  return savedPlans.value.slice(0, collapsedPlanCount);
});

function cityCoverStyle(coverImage) {
  const fallback = "linear-gradient(135deg, rgba(10, 94, 99, 0.95), rgba(223, 127, 50, 0.82))";
  return coverImage
    ? {
        backgroundImage: `linear-gradient(135deg, rgba(18, 57, 74, 0.28), rgba(10, 94, 99, 0.12)), url('${coverImage}')`,
      }
    : { backgroundImage: fallback };
}

function buildMatches(keyword) {
  const raw = keyword.trim();
  if (!raw) return cityOptions.value.slice(0, 8);
  return cityOptions.value
    .map((city) => {
      const nameScore = city.name.includes(raw) ? (city.name.startsWith(raw) ? 3 : 2) : 0;
      const provinceScore = city.province?.includes(raw) ? 1 : 0;
      return { ...city, matchScore: nameScore + provinceScore };
    })
    .filter((city) => city.matchScore > 0)
    .sort((a, b) => b.matchScore - a.matchScore || (b.attraction_count || 0) - (a.attraction_count || 0))
    .slice(0, 8);
}

const filteredTargetCities = computed(() => buildMatches(targetKeyword.value));
const filteredDepartureCities = computed(() => buildMatches(departureKeyword.value));

function toggleInterest(item) {
  const index = form.interests.indexOf(item);
  if (index >= 0) {
    form.interests.splice(index, 1);
  } else {
    form.interests.push(item);
  }
}

function selectTargetCity(city) {
  targetKeyword.value = city.name;
  form.target_city = city.name;
  targetMenuOpen.value = false;
}

function selectDepartureCity(city) {
  departureKeyword.value = city.name;
  form.departure_city = city.name;
  departureMenuOpen.value = false;
}

function closeMenuLater(type) {
  window.setTimeout(() => {
    if (type === "target") targetMenuOpen.value = false;
    if (type === "departure") departureMenuOpen.value = false;
  }, 120);
}

function resetForm() {
  const nextState = defaultFormState();
  Object.assign(form, nextState);
  targetKeyword.value = nextState.target_city;
  departureKeyword.value = nextState.departure_city || getDefaultDepartureCity();
  form.departure_city = departureKeyword.value;
  errorMessage.value = "";
  result.value = null;
  activePlanId.value = null;
  plansExpanded.value = false;
  historyMessage.value = "";
  clearPlannerState();
}

let loadingTicker = null;

function startLoadingTicker() {
  loadingStepIndex.value = 0;
  if (loadingTicker) {
    window.clearInterval(loadingTicker);
  }
  loadingTicker = window.setInterval(() => {
    loadingStepIndex.value = (loadingStepIndex.value + 1) % loadingSteps.length;
  }, 1400);
}

function stopLoadingTicker() {
  if (loadingTicker) {
    window.clearInterval(loadingTicker);
    loadingTicker = null;
  }
}

function buildRequestPayload() {
  const payload = {
    target_city: form.target_city,
    departure_city: form.departure_city,
    duration_days: Number(form.duration_days),
    season_hint: form.season_hint,
    budget_level: form.budget_level,
    companions: form.companions,
    interests: form.interests.length ? [...form.interests] : [...defaultInterests],
    mode: form.mode,
    save_plan: Boolean(authState.user),
  };
  const matchedCity = cityOptions.value.find((item) => item.name === payload.target_city);
  if (matchedCity) {
    payload.city_id = matchedCity.id;
  }
  return payload;
}

async function loadSavedPlans() {
  if (!authState.user) {
    savedPlans.value = [];
    activePlanId.value = null;
    return;
  }

  loadingPlans.value = true;
  historyMessage.value = "";
  try {
    const plans = await getTravelPlans();
    savedPlans.value = plans.filter((item) => Number(item.user) === Number(authState.user?.id));
    if (activePlanId.value && !savedPlans.value.some((item) => item.id === activePlanId.value)) {
      activePlanId.value = null;
    }
  } catch {
    historyMessage.value = "历史行程加载失败，请稍后刷新。";
  } finally {
    loadingPlans.value = false;
  }
}

function restoreSavedPlan(plan) {
  const requestPayload = buildPlannerRequestFromSavedPlan(plan);
  const restoredResult = normalizePlannerResult({
    ...plan,
    city: plan.city_detail,
    matched_city_name: plan.city_detail?.name || "",
    planner_mode: "saved_plan",
    planner_strategy: "saved",
    planner_provider: "saved",
    saved_plan: plan,
  });

  applyRequestPayload(requestPayload);
  result.value = restoredResult;
  errorMessage.value = "";
  activePlanId.value = plan.id;
  persistPlannerState(requestPayload, restoredResult);
}

function formatPlanDate(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "";
}

async function handleSubmit() {
  form.target_city = targetKeyword.value.trim();
  form.departure_city = departureKeyword.value.trim();
  if (!form.target_city || !form.departure_city) return;

  const requestPayload = buildRequestPayload();
  loading.value = true;
  startLoadingTicker();
  errorMessage.value = "";
  result.value = null;
  activePlanId.value = null;
  try {
    const response = await generatePlan(requestPayload);
    result.value = normalizePlannerResult(response);
    activePlanId.value = response.saved_plan?.id || null;
    persistPlannerState(requestPayload, result.value);
    await loadSavedPlans();
  } catch (error) {
    const responseData = error.response?.data || {};
    errorMessage.value = responseData.failure_reason || responseData.detail || "行程生成失败，请稍后重试。";
  } finally {
    loading.value = false;
    stopLoadingTicker();
  }
}

onMounted(async () => {
  cityOptions.value = await getCities({ limit: 500 });
  let restoredFromCache = false;

  if (!targetKeyword.value && route.query.cityId) {
    const matchedCity = cityOptions.value.find((item) => String(item.id) === String(route.query.cityId));
    if (matchedCity) {
      targetKeyword.value = matchedCity.name;
      form.target_city = matchedCity.name;
    }
  }

  if (!departureKeyword.value || !cityOptions.value.find((item) => item.name === departureKeyword.value)) {
    departureKeyword.value = getDefaultDepartureCity();
    form.departure_city = departureKeyword.value;
  }

  restoredFromCache = restorePlannerState();

  await loadSavedPlans();
  if (restoredFromCache) {
    historyMessage.value = "已恢复上一次查看的 AI 行程。";
  }
});

watch(targetKeyword, (value) => {
  form.target_city = value.trim();
});

watch(departureKeyword, (value) => {
  form.departure_city = value.trim();
});

watch(
  () => route.query,
  (query) => {
    if (typeof query.targetCity === "string") {
      targetKeyword.value = query.targetCity;
      form.target_city = query.targetCity;
      return;
    }
    if (query.cityId && cityOptions.value.length) {
      const matchedCity = cityOptions.value.find((item) => String(item.id) === String(query.cityId));
      if (matchedCity) {
        targetKeyword.value = matchedCity.name;
        form.target_city = matchedCity.name;
      }
    }
  },
);

watch(
  () => authState.user?.id || null,
  async () => {
    await loadSavedPlans();
  },
);

onBeforeUnmount(() => {
  stopLoadingTicker();
});
</script>
<style scoped>
.planner-page {
  gap: 24px;
}

.planner-shell {
  display: grid;
  grid-template-columns: minmax(360px, 430px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.planner-control-panel,
.planner-result-panel {
  display: grid;
  gap: 20px;
  padding: 24px;
  border-radius: 32px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(247, 249, 246, 0.88)),
    rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 56px rgba(17, 57, 68, 0.12);
}

.planner-hero-card {
  display: grid;
  gap: 10px;
  padding: 24px;
  border-radius: 26px;
  color: #fff7ef;
  background:
    radial-gradient(circle at top right, rgba(255, 224, 168, 0.3), transparent 28%),
    linear-gradient(135deg, rgba(18, 57, 74, 0.98), rgba(10, 94, 99, 0.92) 58%, rgba(223, 127, 50, 0.88));
}

.planner-eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 245, 230, 0.78);
}

.planner-hero-card h1,
.planner-result-header h2,
.planner-empty-state h3,
.planner-summary-copy h3,
.planner-city-copy h3,
.planner-day-head h3 {
  margin: 0;
  font-family: var(--heading-font);
  font-weight: 600;
}

.planner-hero-card h1 {
  font-size: clamp(30px, 4vw, 42px);
  line-height: 1.08;
}

.planner-hero-copy {
  margin: 0;
  line-height: 1.7;
  color: rgba(255, 247, 238, 0.88);
}

.planner-stat-card,
.planner-bento-card,
.planner-day-card,
.planner-empty-state,
.planner-city-hero,
.planner-summary-hero {
  border: 1px solid rgba(17, 57, 68, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
}

.planner-stat-card span,
.planner-summary-pill span,
.planner-day-kicker,
.planner-block-time {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.planner-stat-card strong,
.planner-summary-pill strong {
  font-size: 18px;
  color: var(--secondary);
}

.planner-stat-card p,
.planner-block-card p,
.planner-empty-state p,
.planner-summary-copy p,
.planner-city-copy p {
  margin: 0;
  line-height: 1.65;
}

.planner-form {
  display: grid;
  gap: 18px;
}

.planner-history-section,
.planner-history-stack,
.planner-history-list,
.planner-history-empty {
  display: grid;
}

.planner-history-stack,
.planner-history-list {
  gap: 12px;
}

.planner-history-head {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.planner-history-toggle {
  white-space: nowrap;
}

.planner-history-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 16px;
  border: 1px solid rgba(17, 57, 68, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  color: var(--secondary);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.planner-history-card:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.22);
}

.planner-history-card.active {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(18, 57, 74, 0.98), rgba(10, 94, 99, 0.92) 56%, rgba(223, 127, 50, 0.88));
  color: white;
}

.planner-history-card.active .muted {
  color: rgba(255, 247, 238, 0.82);
}

.planner-history-copy {
  display: grid;
  gap: 6px;
}

.planner-history-copy p {
  margin: 0;
}

.planner-history-empty {
  gap: 8px;
}

.planner-history-more {
  margin: 0;
}

.planner-form-section {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(246, 244, 238, 0.72), rgba(255, 255, 255, 0.84));
  border: 1px solid rgba(17, 57, 68, 0.08);
}

.planner-section-head {
  display: grid;
  gap: 4px;
}

.planner-section-head span {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}

.planner-section-head strong {
  font-size: 18px;
  color: var(--secondary);
}

.planner-field-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.planner-search-field {
  position: relative;
  min-width: 0;
}

.planner-search-box {
  position: relative;
}

.planner-search-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  z-index: 12;
  display: grid;
  gap: 8px;
  padding: 10px;
  border-radius: 18px;
  border: 1px solid rgba(17, 57, 68, 0.1);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 20px 38px rgba(17, 57, 68, 0.14);
}

.planner-search-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 14px;
  border: 1px solid transparent;
  border-radius: 16px;
  background: rgba(244, 247, 246, 0.94);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.planner-search-option:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.18);
  background: rgba(238, 247, 246, 1);
}

.planner-search-option div {
  display: grid;
  gap: 4px;
}

.planner-search-option span,
.planner-search-option small {
  color: var(--muted);
}

.planner-interest-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.planner-mode-select-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.planner-mode-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid rgba(17, 57, 68, 0.1);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--secondary);
  cursor: pointer;
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.planner-mode-card:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.22);
}

.planner-mode-card strong,
.planner-mode-card p {
  margin: 0;
}

.planner-mode-card p {
  color: var(--muted);
  line-height: 1.6;
  font-size: 13px;
}

.planner-mode-card.active {
  border-color: transparent;
  color: white;
  background: linear-gradient(135deg, rgba(18, 57, 74, 0.98), rgba(10, 94, 99, 0.92) 56%, rgba(223, 127, 50, 0.88));
}

.planner-mode-card.active p {
  color: rgba(255, 247, 238, 0.82);
}

.planner-interest-chip {
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid rgba(17, 57, 68, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--secondary);
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.planner-interest-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.22);
}

.planner-interest-chip.active {
  border-color: transparent;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--accent));
}

.planner-form-footer {
  gap: 12px;
}

.planner-subtle-note {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.planner-error-banner {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(191, 67, 42, 0.1);
  color: #8f2f1c;
}

.planner-submit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.planner-submit-button {
  min-width: 180px;
}

.planner-result-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.planner-result-header p {
  margin: 6px 0 0;
}

.planner-loading-stage,
.planner-result-stack {
  display: grid;
  gap: 18px;
}

.planner-loading-stage {
  min-height: 420px;
  align-content: start;
}

.planner-loading-hero,
.planner-loading-step {
  border: 1px solid rgba(17, 57, 68, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
}

.planner-loading-hero {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 24px;
  padding: 28px;
  background:
    radial-gradient(circle at top right, rgba(255, 224, 168, 0.16), transparent 24%),
    linear-gradient(140deg, rgba(18, 57, 74, 0.98), rgba(10, 94, 99, 0.93) 52%, rgba(223, 127, 50, 0.82));
  color: #fff;
}

.planner-loading-copy {
  display: grid;
  align-content: center;
  gap: 10px;
}

.planner-loading-copy h3,
.planner-loading-copy p {
  margin: 0;
}

.planner-loading-copy p {
  color: rgba(255, 247, 238, 0.86);
  line-height: 1.7;
}

.planner-loading-step-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.planner-loading-step {
  display: grid;
  gap: 8px;
  padding: 18px;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.planner-loading-step span {
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.planner-loading-step p {
  margin: 0;
  color: var(--secondary);
  line-height: 1.6;
}

.planner-loading-step.active {
  transform: translateY(-2px);
  border-color: rgba(223, 127, 50, 0.35);
  background: rgba(255, 248, 239, 0.96);
}

.planner-loading-step.passed {
  border-color: rgba(10, 94, 99, 0.16);
  background: rgba(241, 248, 246, 0.94);
}

.planner-loading-orbit {
  position: relative;
  width: 132px;
  height: 132px;
  margin: auto;
}

.planner-loading-ring,
.planner-loading-core {
  position: absolute;
  inset: 0;
  border-radius: 999px;
}

.planner-loading-ring {
  border: 1px solid rgba(255, 255, 255, 0.28);
}

.planner-loading-ring-a {
  animation: planner-spin 4.8s linear infinite;
}

.planner-loading-ring-b {
  inset: 12px;
  border-color: rgba(255, 214, 150, 0.6);
  animation: planner-spin-reverse 3.6s linear infinite;
}

.planner-loading-ring-c {
  inset: 28px;
  border-color: rgba(255, 255, 255, 0.65);
  animation: planner-spin 2.4s linear infinite;
}

.planner-loading-core {
  inset: 44px;
  background: radial-gradient(circle, rgba(255, 244, 225, 0.98), rgba(255, 206, 122, 0.36));
  box-shadow: 0 0 34px rgba(255, 214, 150, 0.32);
}

.planner-warning-banner {
  margin: 0;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(223, 127, 50, 0.18);
  background: rgba(255, 246, 235, 0.96);
  color: #8b5418;
  line-height: 1.6;
}

.planner-summary-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  padding: 24px;
  color: white;
  background:
    radial-gradient(circle at top right, rgba(255, 224, 168, 0.2), transparent 24%),
    linear-gradient(140deg, rgba(18, 57, 74, 0.98), rgba(10, 94, 99, 0.93) 52%, rgba(223, 127, 50, 0.82));
}

.planner-summary-copy p {
  color: rgba(255, 248, 241, 0.86);
}

.planner-summary-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
}

.planner-summary-pill {
  min-width: 132px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(6px);
}

.planner-summary-pill span {
  color: rgba(255, 245, 230, 0.68);
}

.planner-summary-pill strong {
  display: block;
  margin-top: 6px;
  color: white;
}

.planner-city-hero {
  display: grid;
  grid-template-columns: 196px minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
}

.planner-city-cover {
  min-height: 176px;
  border-radius: 20px;
  background-position: center;
  background-size: cover;
}

.planner-city-copy {
  display: grid;
  align-content: center;
  gap: 10px;
}

.planner-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.planner-stat-grid,
.planner-bento-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.planner-bento-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planner-stat-card {
  display: grid;
  gap: 8px;
  padding: 18px;
}

.planner-bento-card {
  display: grid;
  gap: 14px;
  padding: 20px;
}

.planner-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.planner-spot-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.planner-spot-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(246, 248, 247, 0.96);
  border: 1px solid rgba(17, 57, 68, 0.08);
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.planner-spot-card:hover,
.planner-spot-link:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.16);
}

.planner-spot-card p {
  margin: 0;
  color: var(--muted);
}

.planner-recommendation-zone {
  display: grid;
  gap: 14px;
}

.planner-city-grid {
  align-items: stretch;
}

.planner-itinerary-stack {
  display: grid;
  gap: 16px;
}

.planner-day-card {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.planner-day-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.planner-day-kicker {
  margin: 0 0 8px;
}

.planner-day-head p {
  margin: 6px 0 0;
}

.planner-block-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.planner-block-card {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(249, 247, 242, 0.9), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(17, 57, 68, 0.08);
}

.planner-block-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.planner-spot-link {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: var(--secondary);
}

.planner-period-pill {
  background: rgba(10, 94, 99, 0.08);
}

.planner-block-meta {
  display: grid;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}

.planner-day-footer {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(243, 247, 246, 0.94);
}

.planner-day-footer p {
  margin: 0;
}

.planner-empty-state {
  display: grid;
  place-items: center;
  min-height: 380px;
  padding: 24px;
  text-align: center;
}

@keyframes planner-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes planner-spin-reverse {
  from {
    transform: rotate(360deg);
  }

  to {
    transform: rotate(0deg);
  }
}

@media (max-width: 1240px) {
  .planner-shell {
    grid-template-columns: 1fr;
  }

  .planner-summary-hero,
  .planner-loading-hero,
  .planner-city-hero,
  .planner-bento-grid {
    grid-template-columns: 1fr;
  }

  .planner-stat-grid,
  .planner-block-grid,
  .planner-spot-grid,
  .planner-loading-step-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .planner-loading-hero,
  .planner-stat-grid,
  .planner-block-grid,
  .planner-spot-grid,
  .planner-loading-step-grid {
    grid-template-columns: 1fr;
  }

  .planner-result-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 720px) {
  .planner-control-panel,
  .planner-result-panel {
    padding: 18px;
    border-radius: 24px;
  }

  .planner-hero-card,
  .planner-form-section,
  .planner-loading-hero,
  .planner-summary-hero,
  .planner-day-card,
  .planner-bento-card {
    padding: 18px;
  }

  .planner-field-grid,
  .planner-city-hero,
  .planner-stat-grid,
  .planner-block-grid,
  .planner-spot-grid,
  .planner-loading-step-grid,
  .planner-mode-select-grid {
    grid-template-columns: 1fr;
  }

  .planner-result-header,
  .planner-day-head,
  .planner-summary-hero {
    grid-template-columns: 1fr;
    display: grid;
  }

  .planner-summary-meta {
    display: grid;
    width: 100%;
    justify-content: flex-start;
  }

  .planner-summary-pill,
  .planner-submit-row .btn,
  .planner-submit-button {
    width: 100%;
    min-width: 0;
  }

  .planner-submit-row,
  .planner-card-head,
  .planner-block-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .planner-history-head {
    grid-template-columns: 1fr;
  }

  .planner-search-option {
    align-items: flex-start;
    flex-direction: column;
  }

  .planner-loading-orbit {
    width: 112px;
    height: 112px;
  }

  .planner-empty-state {
    min-height: 260px;
  }
}
</style>





