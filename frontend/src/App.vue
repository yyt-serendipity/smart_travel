<template>
  <div v-if="isBackoffice" class="backoffice-shell">
    <BackofficeSidebar />
    <main class="backoffice-main">
      <div class="backoffice-main-shell">
        <BackofficeHeader />
        <transition :name="transitionName" mode="out-in">
          <RouterView :key="route.fullPath" />
        </transition>
      </div>
    </main>
  </div>

  <div v-else class="app-shell">
    <div class="background-orb orb-left"></div>
    <div class="background-orb orb-right"></div>
    <AppHeader />
    <main class="app-main">
      <div class="container">
        <transition :name="transitionName" mode="out-in">
          <RouterView :key="route.fullPath" />
        </transition>
      </div>
    </main>
    <AssistantChatWidget v-if="showAssistantWidget" />
    <ScrollTopButton />
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { RouterView, useRoute } from "vue-router";

import AppHeader from "./components/AppHeader.vue";
import AssistantChatWidget from "./components/AssistantChatWidget.vue";
import ScrollTopButton from "./components/ScrollTopButton.vue";
import BackofficeHeader from "./components/backoffice/BackofficeHeader.vue";
import BackofficeSidebar from "./components/backoffice/BackofficeSidebar.vue";


const route = useRoute();
const AUTH_ROUTE_ORDER = {
  login: 0,
  register: 1,
};
const authTransitionDirection = ref("forward");

watch(
  () => route.name,
  (currentName, previousName) => {
    const currentIndex = AUTH_ROUTE_ORDER[currentName];
    if (currentIndex === undefined) {
      return;
    }

    const previousIndex = AUTH_ROUTE_ORDER[previousName];
    if (previousIndex === undefined) {
      authTransitionDirection.value = currentIndex > 0 ? "forward" : "back";
      return;
    }

    authTransitionDirection.value = currentIndex >= previousIndex ? "forward" : "back";
  },
  { immediate: true },
);

const isBackoffice = computed(() => route.meta.layout === "admin");
const showAssistantWidget = computed(() => !isBackoffice.value && !["login", "register"].includes(route.name));
const transitionName = computed(() => {
  if (route.meta.transition === "auth-swap") {
    return authTransitionDirection.value === "forward" ? "auth-swap-forward" : "auth-swap-back";
  }
  return route.meta.transition || (isBackoffice.value ? "admin-pane" : "fade-slide");
});
</script>
