<template>
  <section class="page auth-page auth-page-register">
    <div class="auth-layout">
      <AuthShowcase
        eyebrow="Travel Register"
        variant="register"
        title="创建你的旅行档案"
        description="注册后可以保存 AI 行程、发布帖子、积累互动记录，并持续完善个人主页。"
        :highlights="['创建个人主页', '保存 AI 行程', '参与社区互动']"
        :metrics="metrics"
        :floating-notes="['个人主页', '路线收藏', '发帖互动']"
      />

      <article class="card section-shell auth-card auth-form-card">
        <div class="page-toolbar auth-toolbar">
          <RouterLink class="pill auth-switch-link" to="/login">已有账号？去登录</RouterLink>
        </div>

        <SectionHeader
          eyebrow="Auth"
          title="注册"
          description="创建账号后即可发布帖子、保存 AI 行程和维护个人主页。"
        />

        <form class="grid" style="margin-top: 24px" @submit.prevent="handleSubmit">
          <div class="field">
            <label for="nickname">昵称</label>
            <input id="nickname" v-model.trim="form.nickname" autocomplete="nickname" />
          </div>
          <div class="field">
            <label for="username">用户名</label>
            <input id="username" v-model.trim="form.username" autocomplete="username" />
          </div>
          <div class="field">
            <label for="password">密码</label>
            <input id="password" v-model="form.password" type="password" autocomplete="new-password" />
          </div>
          <button class="btn btn-primary" type="submit" :disabled="loading">{{ loading ? "注册中..." : "注册并登录" }}</button>
        </form>

        <p v-if="errorMessage" class="auth-message auth-message-error">{{ errorMessage }}</p>

        <div class="timeline-item" style="margin-top: 20px">
          <strong>注册后即可使用</strong>
          <p class="muted">个人主页、发帖浏览、点赞评论、AI 行程保存和后台管理入口都会同步开启。</p>
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
import { register } from "../services/api";

const router = useRouter();
const loading = ref(false);
const errorMessage = ref("");
const metrics = [
  { value: "AI", label: "智能规划" },
  { value: "Feed", label: "社区信息流" },
  { value: "Admin", label: "后台管理" },
];
const form = reactive({
  nickname: "",
  username: "",
  password: "",
});

function normalizeError(error) {
  const data = error.response?.data;
  if (!data) return "注册失败，请稍后重试。";
  if (typeof data.detail === "string") return data.detail;
  return Object.values(data).flat().join(" ") || "注册失败，请检查输入内容。";
}

async function handleSubmit() {
  loading.value = true;
  errorMessage.value = "";
  try {
    await register(form);
    router.push("/");
  } catch (error) {
    errorMessage.value = normalizeError(error);
  } finally {
    loading.value = false;
  }
}
</script>
