<template>
  <section class="page community-page">
    <article class="card community-hero">
      <div class="community-hero-overlay">
        <span class="eyebrow">Community</span>
        <h1 class="hero-title">旅游社区</h1>
        <p class="hero-subtitle">看城市经验、避坑建议和真实路线，快速找到同城内容。</p>
      </div>
    </article>

    <div class="community-board">
      <aside class="community-side">
        <article class="card section-shell sticky-card">
          <SectionHeader title="筛选帖子" description="按关键词和城市快速缩小范围。" />
          <div class="grid" style="margin-top: 20px">
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
        </article>
      </aside>

      <div class="community-feed">
        <CommunityFeedCard v-for="post in posts" :key="post.id" :post="post" />
      </div>

      <aside class="community-compose">
        <article class="card section-shell sticky-card">
          <SectionHeader title="发布帖子" description="封面、标签和正文会一起展示在社区卡片中。" />
          <form class="grid" style="margin-top: 20px" @submit.prevent="handleCreate">
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
            <div class="field">
              <label for="postTitle">标题</label>
              <input id="postTitle" v-model.trim="form.title" />
            </div>
            <div class="field">
              <label>封面</label>
              <FileUploadField
                v-model="form.cover_image"
                category="post-cover"
                accept=".png,.jpg,.jpeg,.webp,.gif"
                preview-alt="post cover preview"
              />
            </div>
            <div class="field">
              <label>标签</label>
              <div class="tag-selector">
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
            <div class="field">
              <label for="postContent">正文</label>
              <textarea id="postContent" v-model.trim="form.content" class="textarea" rows="8"></textarea>
            </div>
            <button class="btn btn-primary" type="submit" :disabled="!authState.user">发布</button>
          </form>
        </article>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import FileUploadField from "../components/FileUploadField.vue";
import SectionHeader from "../components/SectionHeader.vue";
import CommunityFeedCard from "../components/community/CommunityFeedCard.vue";
import { createPost, getAttractions, getCities, getPosts } from "../services/api";
import { authState } from "../stores/auth";


const route = useRoute();
const keyword = ref("");
const selectedCityId = ref(route.query.cityId ? String(route.query.cityId) : "");
const cityKeyword = ref("");
const cityMenuOpen = ref(false);
const posts = ref([]);
const cityOptions = ref([]);
const attractionOptions = ref([]);
const selectedTags = ref([]);
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
  if (!authState.user) return;
  await createPost({
    ...form,
    tags: selectedTags.value,
  });
  form.attraction = "";
  form.title = "";
  form.cover_image = "";
  form.content = "";
  selectedTags.value = [];
  await loadPosts();
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
