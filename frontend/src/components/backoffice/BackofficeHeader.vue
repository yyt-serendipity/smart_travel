<template>
  <header class="backoffice-topbar card surface-strong">
    <div class="backoffice-topbar-copy">
      <span class="eyebrow">Enterprise Console</span>
      <h1 class="backoffice-topbar-title">{{ currentMeta.title }}</h1>
      <p class="muted">{{ currentMeta.description }}</p>
    </div>

    <div class="backoffice-topbar-actions">
      <span class="pill">{{ currentTime }}</span>
      <a class="btn btn-secondary" href="/site-admin/" target="_blank" rel="noreferrer">Django Admin</a>
      <RouterLink class="btn btn-primary" to="/">用户端首页</RouterLink>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";


const route = useRoute();
const tabMeta = {
  overview: {
    title: "后台工作台",
    description: "参考企业级后台的工作台结构，把总览、状态、日志和操作入口收拢到统一控制面板。",
  },
  users: {
    title: "用户信息管理",
    description: "管理账号状态、个人资料、头像和基础权限，右侧只展示当前模块内容。",
  },
  cities: {
    title: "城市资产中心",
    description: "集中维护城市内容、封面、标签和推荐状态。",
  },
  attractions: {
    title: "景点资产中心",
    description: "集中管理景点图片、结构化资料与来源信息。",
  },
  posts: {
    title: "社区内容审核台",
    description: "统一处理帖子内容、城市关联和社区资产沉淀。",
  },
  logs: {
    title: "系统操作日志",
    description: "审计上传、导入、增删改和 AI 规划的关键操作轨迹。",
  },
};

const currentMeta = computed(() => tabMeta[route.query.tab || "overview"] || tabMeta.overview);
const currentTime = computed(() =>
  new Date().toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }),
);
</script>
