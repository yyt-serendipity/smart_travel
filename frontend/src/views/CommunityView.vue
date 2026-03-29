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
          <div class="grid" style="margin-top: 20px">
            <div class="field">
              <label for="search">鎼滅储甯栧瓙</label>
              <input id="search" v-model.trim="keyword" placeholder="搜索标题或正文" />
            </div>

            <div class="field planner-search-field">
              <label for="citySearch">按城市筛选</label>
              <div class="planner-search-box">
                <input
                  id="citySearch"
                  v-model.trim="cityKeyword"
                  autocomplete="off"
                  placeholder="鎼滅储鍩庡競鍚庨€夋嫨"
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
            <button class="btn btn-primary community-publish-button" type="button" @click="openComposer">发布帖子</button>
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
    </div>

    <transition name="fade-slide">
      <div v-if="composerOpen" class="community-modal-overlay" @click.self="closeComposer">
        <section ref="composerModalRef" class="community-modal card surface-strong">
          <div class="community-modal-head">
            <div class="community-modal-head-copy">
              <p class="assistant-kicker">Post Studio</p>
              <h2>发布帖子</h2>
              <p class="muted">把基础信息、封面和正文放进一个更清晰的编辑弹窗里完成。</p>
            </div>

            <div class="community-modal-head-actions">
              <div class="community-modal-badges">
                <span class="pill">{{ selectedFormCityName || "未选城市" }}</span>
                <span class="pill">{{ selectedTags.length }} 个标签</span>
                <span class="pill">{{ previewText.length }} 字摘要</span>
              </div>
              <button class="community-modal-close" type="button" aria-label="关闭发布窗口" @click="closeComposer">×</button>
            </div>
          </div>

          <div class="community-modal-layout">
            <form class="community-modal-form" @submit.prevent="handleCreate">
              <section class="community-form-section">
                <div class="community-form-section-head">
                  <div>
                    <p class="community-section-kicker">Step 1</p>
                    <h3>基本信息</h3>
                  </div>
                  <span class="pill">先确定城市和标题</span>
                </div>

                <div class="field-grid community-compose-grid">
                  <div class="field">
                    <label for="postCity">关联城市</label>
                    <select id="postCity" v-model="form.city">
                      <option value="">不关联</option>
                      <option v-for="city in cityOptions" :key="city.id" :value="city.id">{{ city.name }}</option>
                    </select>
                  </div>

                  <div class="field">
                    <label for="postAttraction">关联景点</label>
                    <select id="postAttraction" v-model="form.attraction" :disabled="!form.city">
                      <option value="">不关联</option>
                      <option v-for="item in attractionOptions" :key="item.id" :value="item.id">{{ item.name }}</option>
                    </select>
                  </div>
                </div>

                <div class="field">
                  <label for="postTitle">标题</label>
                  <input id="postTitle" v-model.trim="form.title" placeholder="给这篇帖子起一个清晰的标题" />
                </div>
              </section>

              <section class="community-form-section">
                <div class="community-form-section-head">
                  <div>
                    <p class="community-section-kicker">Step 2</p>
                    <h3>封面与标签</h3>
                  </div>
                  <span class="pill">强化卡片展示效果</span>
                </div>

                <div class="field">
                  <label>封面</label>
                  <FileUploadField
                    v-model="form.cover_image"
                    category="post-cover"
                    accept=".png,.jpg,.jpeg,.webp,.gif"
                    helper="建议上传横向封面，社区卡片展示更稳定。"
                    preview-alt="post cover preview"
                  />
                </div>

                <div class="field">
                  <label>标签</label>
                  <div class="tag-selector community-tag-selector">
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
              </section>

              <section class="community-form-section community-form-section-richtext">
                <div class="community-form-section-head">
                  <div>
                    <p class="community-section-kicker">Step 3</p>
                    <h3>正文内容</h3>
                  </div>
                  <span class="pill">支持富文本排版</span>
                </div>

                <div class="field">
                  <label>正文</label>
                  <RichTextEditor
                    v-model="form.content"
                    placeholder="写下你的路线、体验、预算提示、交通建议或避坑提醒。"
                  />
                </div>
              </section>

              <p v-if="createError" class="planner-error-banner">{{ createError }}</p>

              <div class="community-modal-actions">
                <div class="community-modal-status">
                  <strong>{{ authState.user ? "可以直接发布" : "请先登录" }}</strong>
                  <span class="muted">{{ authState.user ? "发布后会立即出现在社区动态中。" : "登录后即可发布帖子。" }}</span>
                </div>
                <div class="community-modal-actions-right">
                  <button class="btn btn-secondary" type="button" @click="closeComposer">取消</button>
                  <button class="btn btn-primary" type="submit" :disabled="creatingPost || !authState.user">
                    {{ creatingPost ? "发布中..." : "发布帖子" }}
                  </button>
                </div>
              </div>
            </form>

            <aside class="community-modal-side">
              <article class="community-preview-card">
                <div class="community-preview-cover" :style="previewCoverStyle">
                  <div class="community-preview-overlay">
                    <span class="pill">实时预览</span>
                    <strong>{{ form.title || "你的帖子标题会显示在这里" }}</strong>
                    <p>{{ selectedFormCityName || "未关联城市" }}<template v-if="selectedAttractionName"> · {{ selectedAttractionName }}</template></p>
                  </div>
                </div>

                <div class="community-preview-body">
                  <div class="community-preview-metrics">
                    <div class="community-preview-metric">
                      <span>标签</span>
                      <strong>{{ selectedTags.length }}</strong>
                    </div>
                    <div class="community-preview-metric">
                      <span>摘要</span>
                      <strong>{{ previewText.length }}</strong>
                    </div>
                  </div>

                  <RichTextContent
                    class="community-preview-text"
                    variant="compact"
                    :html="form.content"
                    empty-text="这里会显示正文预览。建议把路线、体验、预算和实用提醒写完整。"
                    clamp
                  />
                  <div class="chip-row">
                    <span v-for="tag in selectedTags.slice(0, 6)" :key="tag" class="tag-pill">{{ tag }}</span>
                  </div>
                </div>
              </article>

              <article class="community-guide-card">
                <h3>发布建议</h3>
                <ul>
                  <li>标题先写清城市和路线主题。</li>
                  <li>正文尽量包含交通、预算和避坑信息。</li>
                  <li>封面建议用横向图，列表卡片展示更完整。</li>
                </ul>
              </article>
            </aside>
          </div>
        </section>
      </div>
    </transition>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import FileUploadField from "../components/FileUploadField.vue";
import RichTextContent from "../components/RichTextContent.vue";
import RichTextEditor from "../components/RichTextEditor.vue";
import SectionHeader from "../components/SectionHeader.vue";
import CommunityFeedCard from "../components/community/CommunityFeedCard.vue";
import { createPost, getAttractions, getCities, getPosts } from "../services/api";
import { authState } from "../stores/auth";
import { hasRichTextContent, stripHtml } from "../utils/richText";

const route = useRoute();
const keyword = ref("");
const selectedCityId = ref(route.query.cityId ? String(route.query.cityId) : "");
const cityKeyword = ref("");
const cityMenuOpen = ref(false);
const composerOpen = ref(false);
const creatingPost = ref(false);
const createError = ref("");
const posts = ref([]);
const cityOptions = ref([]);
const attractionOptions = ref([]);
const selectedTags = ref([]);
const composerModalRef = ref(null);
const defaultPostTags = ["城市漫步", "周末出游", "亲子", "美食", "拍照", "自然风光", "历史人文", "避坑", "交通", "住宿", "预算", "徒步"];
const form = reactive({
  city: route.query.cityId ? Number(route.query.cityId) : "",
  attraction: "",
  title: "",
  cover_image: "",
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

const selectedFormCityName = computed(() => cityOptions.value.find((item) => Number(item.id) === Number(form.city))?.name || "");
const selectedAttractionName = computed(() => attractionOptions.value.find((item) => Number(item.id) === Number(form.attraction))?.name || "");
const previewText = computed(() => {
  const plain = stripHtml(form.content || "");
  if (!plain) return "";
  return plain.length > 140 ? `${plain.slice(0, 139).trimEnd()}...` : plain;
});
const previewCoverStyle = computed(() => ({
  background: form.cover_image
    ? `linear-gradient(180deg, rgba(9, 34, 43, 0.18), rgba(9, 34, 43, 0.84)), url(${form.cover_image}) center/cover`
    : "linear-gradient(135deg, #103d4b, #0d5c63 58%, #f28f3b)",
}));

function lockBodyScroll(locked) {
  document.body.style.overflow = locked ? "hidden" : "";
}

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

function openComposer() {
  composerOpen.value = true;
  createError.value = "";
  if (!form.city && selectedCityId.value) {
    form.city = Number(selectedCityId.value);
  }
}

function closeComposer() {
  composerOpen.value = false;
  createError.value = "";
}

function resetComposerForm() {
  form.attraction = "";
  form.title = "";
  form.cover_image = "";
  form.content = "";
  selectedTags.value = [];
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
  if (!hasRichTextContent(form.content)) {
    createError.value = "正文不能为空。";
    return;
  }

  creatingPost.value = true;
  createError.value = "";

  try {
    await createPost({
      ...form,
      tags: selectedTags.value,
    });
    resetComposerForm();
    closeComposer();
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
      form.city = cityId ? Number(cityId) : "";
    }
  },
);
watch(composerOpen, async (value) => {
  lockBodyScroll(value);
  if (value) {
    await nextTick();
    composerModalRef.value?.scrollTo({ top: 0, behavior: "auto" });
  }
});

onMounted(async () => {
  cityOptions.value = await getCities({ limit: 500 });
  if (selectedCityId.value) {
    const matched = cityOptions.value.find((item) => String(item.id) === selectedCityId.value);
    if (matched) cityKeyword.value = matched.name;
  }
  await loadAttractions();
  await loadPosts();
});

onBeforeUnmount(() => {
  lockBodyScroll(false);
});
</script>

<style scoped>
.community-board-compact {
  grid-template-columns: 280px minmax(0, 1fr);
}

.community-filter-card {
  display: grid;
  gap: 0;
}

.community-publish-trigger {
  display: grid;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(13, 92, 99, 0.08);
}

.community-publish-button {
  width: 100%;
}

.community-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 44;
  display: grid;
  place-items: center;
  overflow-y: auto;
  padding: 24px;
  background:
    radial-gradient(circle at top, rgba(242, 143, 59, 0.12), transparent 30%),
    rgba(8, 23, 30, 0.62);
  backdrop-filter: blur(12px);
}

.community-modal {
  width: min(1180px, calc(100vw - 32px));
  max-height: calc(100vh - 36px);
  display: grid;
  gap: 22px;
  padding: 26px;
  border-radius: 32px;
  overflow-y: auto;
  overflow-x: hidden;
  background:
    radial-gradient(circle at top right, rgba(242, 143, 59, 0.08), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 247, 0.94));
}

.community-modal-head {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 0 10px;
  background: linear-gradient(180deg, rgba(247, 249, 246, 0.98), rgba(247, 249, 246, 0.9));
}

.community-modal-head-copy {
  display: grid;
  gap: 10px;
}

.community-modal-head h2,
.community-modal-head p,
.community-form-section-head h3,
.community-guide-card h3 {
  margin: 0;
}

.community-modal-head-actions {
  display: grid;
  justify-items: end;
  gap: 12px;
}

.community-modal-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.community-modal-close {
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 14px;
  background: rgba(10, 94, 99, 0.08);
  color: var(--secondary);
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.community-modal-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.72fr);
  gap: 22px;
  align-items: start;
}

.community-modal-form {
  display: grid;
  gap: 18px;
}

.community-form-section {
  display: grid;
  gap: 18px;
  padding: 20px;
  border: 1px solid rgba(13, 92, 99, 0.08);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(245, 249, 248, 0.86));
}

.community-form-section-richtext {
  gap: 14px;
}

.community-form-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.community-section-kicker {
  margin: 0 0 8px;
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.community-compose-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.community-tag-selector {
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(13, 92, 99, 0.1);
  background: rgba(255, 255, 255, 0.84);
}

.community-modal-actions {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(13, 92, 99, 0.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(247, 249, 246, 0.98), rgba(247, 249, 246, 0.94));
}

.community-modal-status {
  display: grid;
  gap: 4px;
}

.community-modal-status strong {
  font-size: 0.98rem;
}

.community-modal-actions-right {
  display: flex;
  gap: 10px;
}

.community-modal-side {
  display: grid;
  gap: 18px;
  align-self: start;
  position: sticky;
  top: 94px;
}

.community-preview-card,
.community-guide-card {
  border: 1px solid rgba(13, 92, 99, 0.08);
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.9);
  overflow: hidden;
}

.community-preview-cover {
  min-height: 230px;
  display: grid;
  align-content: end;
}

.community-preview-overlay {
  display: grid;
  gap: 10px;
  padding: 22px;
  color: white;
}

.community-preview-overlay strong {
  font-size: 1.35rem;
  line-height: 1.35;
}

.community-preview-overlay p,
.community-preview-text,
.community-guide-card ul {
  margin: 0;
}

.community-preview-body {
  display: grid;
  gap: 16px;
  padding: 20px 22px 22px;
}

.community-preview-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.community-preview-metric {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(10, 94, 99, 0.06), rgba(242, 143, 59, 0.12));
}

.community-preview-metric span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.community-preview-text {
  color: var(--muted);
  line-height: 1.75;
}

.community-guide-card {
  display: grid;
  gap: 14px;
  padding: 20px 22px;
}

.community-guide-card ul {
  display: grid;
  gap: 10px;
  padding-left: 18px;
  color: var(--muted);
  line-height: 1.7;
}

@media (max-width: 1180px) {
  .community-board-compact,
  .community-modal-layout {
    grid-template-columns: 1fr;
  }

  .community-modal-side {
    position: static;
  }
}

@media (max-width: 720px) {
  .community-modal-overlay {
    padding: 16px;
  }

  .community-modal {
    width: min(100%, calc(100vw - 12px));
    max-height: calc(100vh - 16px);
    padding: 18px;
    border-radius: 24px;
  }

  .community-modal-head,
  .community-form-section-head,
  .community-modal-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .community-modal-head-actions,
  .community-modal-badges {
    justify-items: stretch;
    justify-content: flex-start;
  }

  .community-compose-grid,
  .community-preview-metrics {
    grid-template-columns: 1fr;
  }

  .community-modal-actions-right {
    width: 100%;
  }

  .community-modal-actions-right > * {
    flex: 1 1 auto;
  }
}
</style>
