<template>
  <header class="header-wrap">
    <div class="container">
      <div class="header card surface-strong" :class="{ open: menuOpen }">
        <div class="header-brand-row">
          <RouterLink class="brand-link" to="/">
            <AppLogo title="China Travel Compass" subtitle="中国城市与景点智能旅行平台" />
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

        <div class="header-menu-shell" :class="{ open: menuOpen }">
          <nav class="nav-links">
            <RouterLink v-for="item in items" :key="item.to" class="nav-link" :to="item.to">
              {{ item.label }}
            </RouterLink>
          </nav>

          <div class="nav-actions">
            <RouterLink v-if="authState.user?.is_staff" class="btn btn-secondary nav-action-button" to="/backoffice">
              后台管理
            </RouterLink>
            <RouterLink v-if="authState.user" class="btn btn-secondary nav-action-button nav-profile-link" to="/profile">
              <span class="nav-profile-avatar">
                <img v-if="authState.user.avatar_url" :src="authState.user.avatar_url" :alt="authState.user.nickname || '用户头像'" />
                <span v-else>{{ authState.user.nickname?.slice(0, 1) || "游" }}</span>
              </span>
              <span>{{ authState.user.nickname || "个人主页" }}</span>
            </RouterLink>
            <RouterLink v-if="!authState.user" class="btn btn-secondary nav-action-button" to="/login">登录</RouterLink>
            <RouterLink v-if="!authState.user" class="btn btn-primary nav-action-button" to="/register">注册</RouterLink>
            <button v-if="authState.user" class="btn btn-primary nav-action-button" type="button" @click="handleLogout">退出</button>
          </div>
        </div>
      </div>
    </div>

    <button v-if="menuOpen" class="nav-backdrop" type="button" aria-label="关闭导航菜单" @click="menuOpen = false"></button>
  </header>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import { logout } from "../services/api";
import { authState } from "../stores/auth";
import AppLogo from "./AppLogo.vue";

const MOBILE_BREAKPOINT = 980;

const route = useRoute();
const router = useRouter();
const menuOpen = ref(false);
const items = [
  { label: "首页", to: "/" },
  { label: "城市推荐", to: "/cities" },
  { label: "景点总览", to: "/attractions" },
  { label: "AI 规划", to: "/planner" },
  { label: "旅行社区", to: "/community" },
];

function closeMenu() {
  menuOpen.value = false;
}

function syncBodyScrollLock(locked) {
  document.body.style.overflow = locked ? "hidden" : "";
}

function handleResize() {
  if (window.innerWidth > MOBILE_BREAKPOINT && menuOpen.value) {
    closeMenu();
  }
}

function handleKeydown(event) {
  if (event.key === "Escape") {
    closeMenu();
  }
}

watch(
  () => route.fullPath,
  () => {
    closeMenu();
  },
);

watch(menuOpen, (value) => {
  syncBodyScrollLock(value && window.innerWidth <= MOBILE_BREAKPOINT);
});

onMounted(() => {
  window.addEventListener("resize", handleResize, { passive: true });
  window.addEventListener("keydown", handleKeydown);
});

onBeforeUnmount(() => {
  syncBodyScrollLock(false);
  window.removeEventListener("resize", handleResize);
  window.removeEventListener("keydown", handleKeydown);
});

async function handleLogout() {
  await logout();
  closeMenu();
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
  position: relative;
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

.header.open {
  box-shadow: 0 28px 56px rgba(17, 57, 68, 0.16);
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

.header-menu-shell {
  display: contents;
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
  flex-shrink: 0;
}

.nav-toggle span {
  width: 18px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.header.open .nav-toggle span:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}

.header.open .nav-toggle span:nth-child(2) {
  opacity: 0;
}

.header.open .nav-toggle span:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

.nav-backdrop {
  display: none;
}

@media (max-width: 980px) {
  .header-wrap {
    padding-inline: 14px;
  }

  .header {
    grid-template-columns: 1fr;
    gap: 0;
    padding: 12px;
    border-radius: 24px;
  }

  .header-menu-shell {
    display: grid;
    gap: 12px;
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: max-height 0.28s ease, opacity 0.2s ease, padding-top 0.2s ease;
  }

  .header-menu-shell.open {
    max-height: calc(100vh - 120px);
    opacity: 1;
    padding-top: 14px;
  }

  .nav-toggle {
    display: inline-flex;
  }

  .nav-links,
  .nav-actions {
    display: grid;
    justify-content: stretch;
    gap: 10px;
    padding: 0;
    background: transparent;
  }

  .nav-actions {
    padding-top: 12px;
    border-top: 1px solid rgba(17, 57, 68, 0.08);
  }

  .nav-link,
  .nav-action-button {
    width: 100%;
    min-height: 50px;
    justify-content: flex-start;
    padding-inline: 16px;
  }

  .nav-link.router-link-active {
    box-shadow: none;
  }

  .nav-profile-link {
    justify-content: flex-start;
  }

  .nav-backdrop {
    position: fixed;
    inset: 0;
    display: block;
    padding: 0;
    border: 0;
    background: rgba(17, 57, 68, 0.14);
    backdrop-filter: blur(6px);
    z-index: 23;
  }
}

@media (max-width: 640px) {
  .header-wrap {
    top: 8px;
    padding-top: 10px;
    padding-inline: 12px;
  }

  .header {
    border-radius: 22px;
  }

  .brand-link :deep(.app-logo-copy small) {
    display: none;
  }

  .brand-link :deep(.app-logo-mark) {
    width: 46px;
    height: 46px;
    border-radius: 16px;
  }

  .brand-link :deep(.app-logo-mark svg) {
    width: 30px;
    height: 30px;
  }

  .nav-actions {
    gap: 8px;
  }
}
</style>
