<template>
  <header class="header-wrap">
    <div class="container">
      <div class="header card surface-strong" :class="{ open: menuOpen }">
        <div class="header-brand-row">
          <RouterLink class="brand-link" to="/">
            <AppLogo title="China Travel Compass" subtitle="中国城市与景点智能旅游平台" />
          </RouterLink>

          <button
            class="nav-toggle"
            type="button"
            :aria-expanded="menuOpen ? 'true' : 'false'"
            aria-label="切换导航菜单"
            @click="menuOpen = !menuOpen"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>

        <nav class="nav-links" :class="{ open: menuOpen }">
          <RouterLink v-for="item in items" :key="item.to" class="nav-link" :to="item.to">
            {{ item.label }}
          </RouterLink>
        </nav>

        <div class="nav-actions" :class="{ open: menuOpen }">
          <RouterLink v-if="authState.user?.is_staff" class="btn btn-secondary nav-action-button" to="/backoffice">后台管理</RouterLink>
          <RouterLink v-if="authState.user" class="btn btn-secondary nav-action-button nav-profile-link" to="/profile">
            <span class="nav-profile-avatar">
              <img v-if="authState.user.avatar_url" :src="authState.user.avatar_url" :alt="authState.user.nickname || '用户头像'" />
              <span v-else>{{ authState.user.nickname?.slice(0, 1) || "旅" }}</span>
            </span>
            <span>{{ authState.user.nickname || "个人主页" }}</span>
          </RouterLink>
          <RouterLink v-if="!authState.user" class="btn btn-secondary nav-action-button" to="/login">登录</RouterLink>
          <RouterLink v-if="!authState.user" class="btn btn-primary nav-action-button" to="/register">注册</RouterLink>
          <button v-if="authState.user" class="btn btn-primary nav-action-button" type="button" @click="handleLogout">退出</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { logout } from "../services/api";
import { authState } from "../stores/auth";
import AppLogo from "./AppLogo.vue";


const route = useRoute();
const router = useRouter();
const menuOpen = ref(false);
const items = [
  { label: "首页", to: "/" },
  { label: "城市推荐", to: "/cities" },
  { label: "景点总览", to: "/attractions" },
  { label: "AI 规划", to: "/planner" },
  { label: "旅游社区", to: "/community" },
];

watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false;
  },
);

async function handleLogout() {
  await logout();
  router.push("/");
}
</script>

<style scoped>
.header-wrap {
  position: sticky;
  top: 12px;
  z-index: 24;
  padding: 16px 20px 0;
}

.header {
  display: grid;
  grid-template-columns: minmax(0, auto) minmax(0, 1fr) minmax(0, auto);
  align-items: center;
  gap: 18px;
  padding: 14px 18px;
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(250, 252, 252, 0.86)),
    radial-gradient(circle at top right, rgba(242, 143, 59, 0.12), transparent 34%);
}

.header-brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand-link {
  min-width: 0;
}

.nav-links {
  justify-content: center;
  gap: 10px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(13, 92, 99, 0.05);
}

.nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  color: var(--muted);
  font-weight: 600;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.nav-link:hover {
  color: var(--primary);
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  color: white;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 12px 24px rgba(13, 92, 99, 0.18);
}

.nav-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.nav-action-button {
  min-height: 44px;
}

.nav-profile-link {
  gap: 10px;
}

.nav-profile-avatar {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--secondary), var(--accent));
  color: white;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.nav-profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.nav-toggle {
  display: none;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0;
  border: 0;
  border-radius: 14px;
  color: var(--primary);
  cursor: pointer;
  background: rgba(13, 92, 99, 0.08);
  flex-direction: column;
}

.nav-toggle span {
  width: 18px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
}

@media (max-width: 1180px) {
  .header {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .nav-toggle {
    display: inline-flex;
  }

  .nav-links,
  .nav-actions {
    display: none;
  }

  .nav-links.open,
  .nav-actions.open {
    display: flex;
  }

  .nav-links.open {
    justify-content: flex-start;
  }

  .nav-actions.open {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .header-wrap {
    padding-inline: 14px;
  }

  .header {
    padding: 12px;
    border-radius: 24px;
  }

  .nav-links.open,
  .nav-actions.open {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-link,
  .nav-action-button {
    width: 100%;
  }
}
</style>
