<template>
  <section class="page profile-page">
    <article class="card section-shell profile-editor-card">
      <div class="profile-editor-shell">
        <div class="profile-avatar-column">
          <span class="eyebrow">Profile</span>
          <h1 class="section-title">个人主页</h1>

          <label class="profile-avatar-panel">
            <input ref="avatarInput" class="profile-avatar-input" type="file" accept=".png,.jpg,.jpeg,.webp,.gif" @change="handleAvatarChange" />
            <span class="profile-avatar-trigger">
              <img v-if="profile.avatar_url" :src="profile.avatar_url" alt="avatar" />
              <span v-else>{{ profile.nickname?.slice(0, 1) || "旅" }}</span>
              <em>{{ avatarUploading ? "上传中..." : "点击更换头像" }}</em>
            </span>
          </label>
          <p v-if="avatarError" class="file-upload-error">{{ avatarError }}</p>

          <div class="mini-spot profile-identity-card">
            <strong>{{ profile.nickname || "旅行者" }}</strong>
            <p class="muted">{{ selectedCityLabel }}</p>
            <p class="muted">{{ profile.favorite_styles.length ? `已选择 ${profile.favorite_styles.length} 个旅行风格` : "完善偏好后会让推荐更贴近你" }}</p>
          </div>
        </div>

        <form class="profile-editor-form" @submit.prevent="handleSave">
          <div class="profile-form-heading">
            <strong>编辑资料</strong>
            <p class="muted">头像、昵称、常住地和偏好会同步到导航栏与社区展示。</p>
          </div>

          <div class="field-grid">
            <div class="field">
              <label for="nickname">昵称</label>
              <input id="nickname" v-model.trim="profile.nickname" />
            </div>
          </div>

          <div class="profile-location-row">
            <div class="field">
              <label for="provinceSelect">省份</label>
              <select id="provinceSelect" v-model="selectedProvince">
                <option value="">请选择省份</option>
                <option v-for="province in provinceOptions" :key="province" :value="province">{{ province }}</option>
              </select>
            </div>

            <div class="field">
              <label for="citySelect">城市</label>
              <select id="citySelect" v-model="profile.home_city_id" :disabled="!selectedProvince">
                <option value="">请选择城市</option>
                <option v-for="city in filteredCityOptions" :key="city.id" :value="String(city.id)">{{ city.name }}</option>
              </select>
            </div>
          </div>

          <div class="field">
            <label>偏好风格</label>
            <div class="profile-style-panel">
              <div class="chip-row">
                <button
                  v-for="style in PROFILE_STYLE_OPTIONS"
                  :key="style"
                  class="chip"
                  :class="{ active: profile.favorite_styles.includes(style) }"
                  type="button"
                  @click="toggleStyle(style)"
                >
                  {{ style }}
                </button>
              </div>
            </div>
          </div>

          <div class="field">
            <label for="bio">简介</label>
            <textarea
              id="bio"
              v-model.trim="profile.bio"
              class="textarea"
              rows="4"
              placeholder="可以写下你的旅行偏好、常去城市，或者想分享的内容。"
            ></textarea>
          </div>

          <div class="profile-save-panel">
            <div class="profile-save-copy">
              <strong>保存后立即同步</strong>
              <p class="muted">资料会更新到个人主页、导航头像和帖子作者信息。</p>
              <p v-if="saveMessage" class="profile-save-message">{{ saveMessage }}</p>
            </div>
            <button class="btn btn-primary profile-save-button" type="submit" :disabled="saving">
              {{ saving ? "保存中..." : "保存个人资料" }}
            </button>
          </div>
        </form>
      </div>
    </article>

    <article class="card section-shell profile-post-section">
      <div class="title-row">
        <SectionHeader title="我的收藏" description="收藏的帖子会和你发布的帖子保持同一展示样式。" />
        <span class="pill">{{ favoritePosts.length }} 篇</span>
      </div>
      <div v-if="favoritePosts.length" class="grid grid-2 profile-post-grid">
        <PostCard v-for="post in favoritePosts" :key="post.id" :post="post" />
      </div>
      <div v-else class="profile-empty-state">
        <strong>还没有收藏的帖子</strong>
      </div>
    </article>

    <article class="card section-shell profile-post-section">
      <div class="title-row">
        <SectionHeader title="我的帖子" description="你发布过的旅行内容会统一展示在这里。" />
        <span class="pill">{{ myPosts.length }} 篇</span>
      </div>
      <div v-if="myPosts.length" class="grid grid-2 profile-post-grid">
        <PostCard v-for="post in myPosts" :key="post.id" :post="post" />
      </div>
      <div v-else class="profile-empty-state">
        <strong>你还没有发布帖子</strong>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";

import PostCard from "../components/PostCard.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { getCities, getFavoritePosts, getPosts, getProfile, updateProfile, uploadMedia } from "../services/api";
import { authState } from "../stores/auth";
import { PROFILE_STYLE_OPTIONS } from "../utils/profileOptions";


const avatarInput = ref(null);
const avatarUploading = ref(false);
const avatarError = ref("");
const saving = ref(false);
const saveMessage = ref("");
const selectedProvince = ref("");
const profile = reactive({
  nickname: "",
  avatar_url: "",
  home_city: "",
  home_city_id: "",
  bio: "",
  favorite_styles: [],
});

const cityOptions = ref([]);
const favoritePosts = ref([]);
const myPosts = ref([]);

const provinceOptions = computed(() =>
  [...new Set(cityOptions.value.map((city) => city.province).filter(Boolean))].sort((a, b) => a.localeCompare(b, "zh-CN")),
);

const filteredCityOptions = computed(() =>
  cityOptions.value
    .filter((city) => !selectedProvince.value || city.province === selectedProvince.value)
    .sort((a, b) => a.name.localeCompare(b.name, "zh-CN")),
);

const selectedHomeCity = computed(() =>
  cityOptions.value.find((city) => city.id === Number(profile.home_city_id || 0)) || null,
);

const selectedCityLabel = computed(() => {
  if (!selectedHomeCity.value) return "未设置";
  return `${selectedHomeCity.value.province || ""} ${selectedHomeCity.value.name}`.trim();
});

function applyProfile(profileData) {
  profile.nickname = profileData.nickname || "";
  profile.avatar_url = profileData.avatar_url || "";
  profile.home_city = profileData.home_city || "";
  profile.home_city_id = profileData.home_city_id ? String(profileData.home_city_id) : "";
  profile.bio = profileData.bio || "";
  profile.favorite_styles = [...(profileData.favorite_styles || [])];
  selectedProvince.value = profileData.home_city_detail?.province || "";
}

function toggleStyle(style) {
  if (profile.favorite_styles.includes(style)) {
    profile.favorite_styles = profile.favorite_styles.filter((item) => item !== style);
    return;
  }
  profile.favorite_styles = [...profile.favorite_styles, style];
}

async function handleAvatarChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  avatarUploading.value = true;
  avatarError.value = "";
  try {
    const result = await uploadMedia(file, "avatar");
    profile.avatar_url = result.url;
  } catch (error) {
    avatarError.value = error?.response?.data?.detail || "头像上传失败，请稍后重试。";
  } finally {
    avatarUploading.value = false;
    event.target.value = "";
  }
}

async function loadData() {
  const [cities, profileData, favoriteData] = await Promise.all([
    getCities({ limit: 500 }),
    getProfile(),
    getFavoritePosts(),
  ]);
  const authorId = profileData.user?.id || authState.user?.id;
  const postData = authorId ? await getPosts({ author_id: authorId }) : [];

  cityOptions.value = cities;
  applyProfile(profileData);
  myPosts.value = postData;
  favoritePosts.value = favoriteData;
}

async function handleSave() {
  saving.value = true;
  saveMessage.value = "";
  try {
    const updatedProfile = await updateProfile({
      nickname: profile.nickname,
      avatar_url: profile.avatar_url,
      bio: profile.bio,
      home_city_id: profile.home_city_id || null,
      favorite_styles: profile.favorite_styles,
    });
    applyProfile(updatedProfile);
    saveMessage.value = "个人资料已更新";
    await loadData();
  } finally {
    saving.value = false;
  }
}

watch(selectedProvince, (province) => {
  if (!province) {
    profile.home_city_id = "";
    return;
  }
  if (!filteredCityOptions.value.some((city) => String(city.id) === String(profile.home_city_id))) {
    profile.home_city_id = "";
  }
});

onMounted(loadData);
</script>
