<template>
  <section class="page community-page">
    <article class="card community-hero">
      <div class="community-hero-overlay">
        <span class="eyebrow">Community</span>
        <h1 class="hero-title">旅游社区</h1>
        <p class="hero-subtitle">看城市经验、避坑建议和真实路线，快速找到同城内容。</p>
      </div>
    </article>

    <div class="community-board community-board-compact">
      <aside class="community-side">
        <article class="card section-shell sticky-card community-filter-card">
          <SectionHeader title="筛选帖子" description="按关键词和城市快速缩小范围。" />
          <div class="grid community-filter-grid">
            <div class="field">
              <label for="search">搜索帖子</label>
              <input id="search" v-model.trim="keyword" placeholder="搜索标题或正文" />
            </div>

            <div class="field planner-search-field">
              <label for="citySearch">按城市筛选</label>
              <div class="planner-search-box">
                <input
                  id="citySearch"
                  v-model.trim="cityKeyword"
                  autocomplete="off"
                  placeholder="搜索城市后选择"
                  @focus="cityMenuOpen = true"
                  @blur="handleCityBlur"
                />
                <div v-if="cityMenuOpen && filteredCities.length" class="planner-search-panel">
                  <button
                    v-for="city in filteredCities"
                    :key="city.id"
                    class="planner-search-option"
                    type="button"
                    @mousedown.prevent="selectCity(city)"
                  >
                    <strong>{{ city.name }}</strong>
                    <span>{{ city.province || "中国" }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="community-publish-trigger">
            <button class="btn btn-primary community-publish-button" type="button" @click="focusComposer">去右侧发帖</button>
          </div>
        </article>
      </aside>

      <div class="community-feed">
        <CommunityFeedCard v-for="post in posts" :key="post.id" :post="post" />
        <article v-if="!posts.length" class="card section-shell page-state">
          <strong>当前筛选下还没有帖子</strong>
          <p class="muted">可以换个城市重新筛选，或者直接发布第一篇内容。</p>
        </article>
      </div>

      <aside class="community-compose">
        <article ref="composerCardRef" class="card section-shell sticky-card community-compose-card">
          <SectionHeader title="快速发帖" description="右侧改为轻量表单，直接填写标题和正文即可，不再使用富文本。" />

          <form class="community-side-compose-form" @submit.prevent="handleCreate">
            <div class="field">
              <label for="sidePostCity">关联城市</label>
              <select id="sidePostCity" v-model="form.city">
                <option value="">不关联</option>
                <option v-for="city in cityOptions" :key="city.id" :value="String(city.id)">{{ city.name }}</option>
              </select>
            </div>

            <div class="field">
              <label for="sidePostAttraction">关联景点</label>
              <select id="sidePostAttraction" v-model="form.attraction" :disabled="!form.city">
                <option value="">不关联</option>
                <option v-for="item in attractionOptions" :key="item.id" :value="String(item.id)">{{ item.name }}</option>
              </select>
            </div>

            <div class="field">
              <label for="sidePostTitle">标题</label>
              <input
                id="sidePostTitle"
                ref="titleInputRef"
                v-model.trim="form.title"
                placeholder="给这篇帖子起一个清晰的标题"
              />
            </div>

            <div class="field">
              <label for="sidePostContent">正文</label>
              <textarea
                id="sidePostContent"
                v-model.trim="form.content"
                class="textarea community-compose-textarea"
                rows="10"
                placeholder="写下路线、体验、预算、交通建议或避坑提醒。"
              ></textarea>
              <p class="muted community-compose-helper">支持纯文本分段，提交后会按段落展示。</p>
            </div>

            <div class="field">
              <label>标签</label>
              <div class="tag-selector community-side-tag-selector">
                <div class="chip-row">
                  <button
                    v-for="tag in postTagOptions"
                    :key="tag"
                    class="chip"
                    :class="{ active: selectedTags.includes(tag) }"
                    type="button"
                    @click="toggleTag(tag)"
                  >
                    {{ tag }}
                  </button>
                </div>
              </div>
            </div>

            <div class="community-compose-summary">
              <span class="pill">{{ selectedFormCityName || "未选城市" }}</span>
              <span class="pill">{{ selectedTags.length }} 个标签</span>
              <span class="pill">{{ contentLength }} 字</span>
            </div>

            <p v-if="createError" class="planner-error-banner">{{ createError }}</p>

            <div class="community-compose-actions">
              <button class="btn btn-secondary" type="button" @click="resetComposerForm">清空</button>
              <button class="btn btn-primary" type="submit" :disabled="creatingPost || !authState.user">
                {{ creatingPost ? "发布中..." : "发布帖子" }}
              </button>
            </div>

            <div class="community-compose-status">
              <strong>{{ authState.user ? "已登录，可直接发布" : "请先登录后再发布" }}</strong>
              <p class="muted">
                {{
                  authState.user
                    ? "这里保留轻量发帖入口，适合快速补充路线、体验和避坑信息。"
                    : "可以先整理内容，登录后再提交。"
                }}
              </p>
            </div>
          </form>
        </article>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import SectionHeader from "../components/SectionHeader.vue";
import CommunityFeedCard from "../components/community/CommunityFeedCard.vue";
import { createPost, getAttractions, getCities, getPosts } from "../services/api";
import { authState } from "../stores/auth";

const route = useRoute();
const keyword = ref("");
const selectedCityId = ref(route.query.cityId ? String(route.query.cityId) : "");
const cityKeyword = ref("");
const cityMenuOpen = ref(false);
const creatingPost = ref(false);
const createError = ref("");
const posts = ref([]);
const cityOptions = ref([]);
const attractionOptions = ref([]);
const selectedTags = ref([]);
const composerCardRef = ref(null);
const titleInputRef = ref(null);
const defaultPostTags = [
  "城市漫步",
  "周末出游",
  "亲子",
  "美食",
  "拍照",
  "自然风光",
  "历史人文",
  "避坑",
  "交通",
  "住宿",
  "预算",
  "徒步",
];
const form = reactive({
  city: route.query.cityId ? String(route.query.cityId) : "",
  attraction: "",
  title: "",
  content: "",
});

const filteredCities = computed(() => {
  const raw = cityKeyword.value.trim();
  if (!raw) return cityOptions.value.slice(0, 8);
  return cityOptions.value
    .filter((city) => city.name.includes(raw) || city.province?.includes(raw))
    .slice(0, 8);
});

const postTagOptions = computed(() => {
  const tags = new Set(defaultPostTags);
  posts.value.forEach((post) => {
    (post.tags || []).forEach((tag) => tags.add(tag));
  });
  return [...tags];
});

const selectedFormCityName = computed(
  () => cityOptions.value.find((item) => String(item.id) === String(form.city))?.name || "",
);
const contentLength = computed(() => form.content.trim().length);

function handleCityBlur() {
  window.setTimeout(() => {
    cityMenuOpen.value = false;
  }, 120);
}

function selectCity(city) {
  cityKeyword.value = city.name;
  selectedCityId.value = String(city.id);
  cityMenuOpen.value = false;
}

async function focusComposer() {
  createError.value = "";
  if (!form.city && selectedCityId.value) {
    form.city = String(selectedCityId.value);
  }
  await nextTick();
  composerCardRef.value?.scrollIntoView({ behavior: "smooth", block: "start" });
  titleInputRef.value?.focus();
}

function resetComposerForm() {
  form.city = selectedCityId.value || "";
  form.attraction = "";
  form.title = "";
  form.content = "";
  selectedTags.value = [];
  createError.value = "";
}

async function loadPosts() {
  posts.value = await getPosts({
    q: keyword.value || undefined,
    city_id: selectedCityId.value || undefined,
  });
}

async function loadAttractions() {
  if (!form.city) {
    attractionOptions.value = [];
    form.attraction = "";
    return;
  }
  attractionOptions.value = await getAttractions({ city_id: form.city, limit: 100 });
}

function toggleTag(tag) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((item) => item !== tag);
    return;
  }
  selectedTags.value = [...selectedTags.value, tag];
}

async function handleCreate() {
  if (!authState.user) {
    createError.value = "请先登录后再发布帖子。";
    return;
  }
  if (!form.title.trim()) {
    createError.value = "标题不能为空。";
    return;
  }
  if (!form.content.trim()) {
    createError.value = "正文不能为空。";
    return;
  }

  creatingPost.value = true;
  createError.value = "";

  try {
    await createPost({
      city: form.city ? Number(form.city) : null,
      attraction: form.attraction ? Number(form.attraction) : null,
      title: form.title,
      content: form.content,
      tags: selectedTags.value,
    });
    resetComposerForm();
    await loadPosts();
  } catch (error) {
    createError.value = error.response?.data?.detail || "帖子发布失败，请稍后重试。";
  } finally {
    creatingPost.value = false;
  }
}

watch([keyword, selectedCityId], loadPosts);
watch(
  () => selectedCityId.value,
  (cityId) => {
    if (!cityId) {
      cityKeyword.value = "";
      return;
    }
    const matched = cityOptions.value.find((item) => String(item.id) === String(cityId));
    if (matched) cityKeyword.value = matched.name;
  },
);
watch(() => form.city, loadAttractions);
watch(
  () => route.query.cityId,
  (cityId) => {
    selectedCityId.value = cityId ? String(cityId) : "";
    if (!form.city) {
      form.city = cityId ? String(cityId) : "";
    }
  },
);

onMounted(async () => {
  cityOptions.value = await getCities({ limit: 500 });
  if (selectedCityId.value) {
    const matched = cityOptions.value.find((item) => String(item.id) === selectedCityId.value);
    if (matched) cityKeyword.value = matched.name;
  }
  await loadAttractions();
  await loadPosts();
});
</script>

<style scoped>
.community-board-compact {
  grid-template-columns: 280px minmax(0, 1fr) 340px;
}

.community-filter-card {
  display: grid;
  gap: 0;
}

.community-filter-grid {
  margin-top: 20px;
}

.community-publish-trigger {
  display: grid;
  gap: 10px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid rgba(13, 92, 99, 0.08);
}

.community-publish-button {
  width: 100%;
}

.community-compose-card {
  display: grid;
  gap: 20px;
  max-height: calc(100vh - 40px);
  overflow: auto;
}

.community-side-compose-form {
  display: grid;
  gap: 16px;
}

.community-compose-textarea {
  min-height: 220px;
  resize: vertical;
}

.community-compose-helper {
  margin: 8px 0 0;
}

.community-side-tag-selector {
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(13, 92, 99, 0.1);
  background: rgba(255, 255, 255, 0.84);
}

.community-compose-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.community-compose-actions {
  display: flex;
  gap: 10px;
}

.community-compose-actions > * {
  flex: 1 1 auto;
}

.community-compose-status {
  display: grid;
  gap: 4px;
  padding: 16px 18px;
  border: 1px solid rgba(13, 92, 99, 0.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(247, 249, 246, 0.98), rgba(247, 249, 246, 0.94));
}

.community-compose-status p {
  margin: 0;
}

@media (max-width: 1180px) {
  .community-board-compact {
    grid-template-columns: 1fr;
  }

  .community-feed {
    order: 1;
  }

  .community-side {
    order: 2;
  }

  .community-compose {
    order: 3;
  }

  .community-compose-card {
    max-height: none;
    position: static;
  }
}

@media (max-width: 720px) {
  .community-compose-actions {
    flex-direction: column;
  }
}
</style>
