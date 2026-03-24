<template>
  <section class="page auth-page auth-page-login">
    <div class="auth-layout">
      <AuthShowcase
        eyebrow="Travel Login"
        variant="login"
        title="进入你的中国旅行空间"
        description="把城市推荐、景点详情、AI 行程和社区内容串成一条完整的旅行体验链路。"
        :highlights="['景点路线 AI 行程', '社区内容互动', '个人主页沉淀']"
        :metrics="metrics"
        :floating-notes="['城市推荐', '景点详情', 'AI 规划']"
      />

      <article class="card section-shell auth-card auth-form-card">
        <div class="page-toolbar auth-toolbar">
          <RouterLink class="pill auth-switch-link" to="/register">还没有账号？去注册</RouterLink>
        </div>

        <SectionHeader
          eyebrow="Auth"
          title="登录"
          description="登录后可以保存行程、发布内容、点赞评论，并进入独立后台。"
        />

        <form class="grid" style="margin-top: 24px" @submit.prevent="handleSubmit">
          <div class="field">
            <label for="username">用户名</label>
            <input id="username" v-model.trim="form.username" autocomplete="username" />
          </div>
          <div class="field">
            <label for="password">密码</label>
            <input id="password" v-model="form.password" type="password" autocomplete="current-password" />
          </div>
          <button class="btn btn-primary" type="submit" :disabled="loading">{{ loading ? "登录中..." : "登录" }}</button>
        </form>

        <p v-if="errorMessage" class="auth-message auth-message-error">{{ errorMessage }}</p>

        <div class="auth-demo-grid">
          <div class="timeline-item">
            <strong>前台体验账号</strong>
            <p class="muted">`traveler / travel123456`</p>
          </div>
          <div class="timeline-item">
            <strong>后台管理账号</strong>
            <p class="muted">`admin / admin123456`</p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import AuthShowcase from "../components/auth/AuthShowcase.vue";
import SectionHeader from "../components/SectionHeader.vue";
import { login } from "../services/api";

const router = useRouter();
const loading = ref(false);
const errorMessage = ref("");
const metrics = [
  { value: "352+", label: "城市数据" },
  { value: "3W+", label: "景点数据" },
  { value: "24h", label: "随时规划" },
];
const form = reactive({
  username: "traveler",
  password: "travel123456",
});

function normalizeError(error) {
  const data = error.response?.data;
  if (!data) return "登录失败，请稍后重试。";
  if (typeof data.detail === "string") return data.detail;
  return Object.values(data).flat().join(" ") || "登录失败，请检查输入内容。";
}

async function handleSubmit() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const data = await login(form);
    router.push(data.user?.is_staff ? "/backoffice" : "/");
  } catch (error) {
    errorMessage.value = normalizeError(error);
  } finally {
    loading.value = false;
  }
}
</script>
