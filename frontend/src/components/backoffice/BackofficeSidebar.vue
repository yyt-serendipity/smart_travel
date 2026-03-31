<template>
  <aside class="backoffice-sidebar">
    <RouterLink class="backoffice-brand" :to="{ name: 'backoffice' }">
      <AppLogo inverse title="Smart Travel" subtitle="后台控制台" />
    </RouterLink>

    <div class="card backoffice-profile-card">
      <div class="backoffice-profile-avatar">{{ (authState.user?.nickname || "A").slice(0, 1) }}</div>
      <div>
        <strong>{{ authState.user?.nickname || "管理员" }}</strong>
        <p class="muted">{{ authState.user?.username || "admin" }}</p>
      </div>
      <div class="chip-row">
        <span class="pill">Enterprise</span>
        <span class="pill">Admin</span>
      </div>
    </div>

    <nav class="backoffice-nav">
      <RouterLink
        v-for="item in items"
        :key="item.tab"
        class="backoffice-link"
        :class="{ active: activeTab === item.tab }"
        :to="{ name: 'backoffice', query: { tab: item.tab } }"
      >
        <span>{{ item.label }}</span>
        <small>{{ item.desc }}</small>
      </RouterLink>
    </nav>

    <div class="backoffice-panel card">
      <RouterLink class="btn btn-primary" to="/">回到用户端</RouterLink>
    </div>
  </aside>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { authState } from "../../stores/auth";
import AppLogo from "../AppLogo.vue";

const items = [
  { tab: "overview", label: "总览", desc: "核心指标与运营总览" },
  { tab: "users", label: "用户", desc: "管理账号与资料" },
  { tab: "cities", label: "城市", desc: "维护城市信息" },
  { tab: "attractions", label: "景点", desc: "管理景点详情" },
  { tab: "posts", label: "社区", desc: "处理帖子内容" },
  { tab: "logs", label: "日志", desc: "查看系统操作记录" },
];

const route = useRoute();
const activeTab = computed(() => route.query.tab || "overview");
</script>
