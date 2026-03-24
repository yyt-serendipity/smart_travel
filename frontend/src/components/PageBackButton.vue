<template>
  <button class="back-button" :class="{ 'back-button-home': isHomeTarget || isTopMode }" type="button" @click="handleBack">
    <span class="back-button-icon" aria-hidden="true">{{ isTopMode ? "↑" : isHomeTarget ? "⌂" : "←" }}</span>
    <span class="back-button-copy">
      <strong>{{ resolvedLabel }}</strong>
      <small v-if="isTopMode">继续浏览当前页面</small>
      <small v-else-if="isHomeTarget">快速回到首页</small>
    </span>
  </button>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";


const props = defineProps({
  label: {
    type: String,
    default: "返回上一页",
  },
  fallbackTo: {
    type: [String, Object],
    default: "/",
  },
  mode: {
    type: String,
    default: "back",
  },
});

const router = useRouter();
const isTopMode = computed(() => props.mode === "top");
const isHomeTarget = computed(() => {
  if (typeof props.fallbackTo === "string") {
    return props.fallbackTo === "/";
  }
  return props.fallbackTo?.name === "home" || props.fallbackTo?.path === "/";
});
const resolvedLabel = computed(() => (isTopMode.value ? props.label || "返回顶部" : props.label));

function handleBack() {
  if (isTopMode.value) {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  if (window.history.length > 1) {
    router.back();
    return;
  }
  router.push(props.fallbackTo);
}
</script>

<style scoped>
.back-button {
  min-height: 50px;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 8px 18px 8px 10px;
  border: 1px solid rgba(10, 94, 99, 0.12);
  border-radius: 999px;
  color: var(--primary);
  cursor: pointer;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(241, 248, 248, 0.92));
  box-shadow: 0 14px 28px rgba(13, 92, 99, 0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.back-button:hover {
  transform: translateY(-1px);
  border-color: rgba(10, 94, 99, 0.2);
  box-shadow: 0 18px 32px rgba(13, 92, 99, 0.14);
}

.back-button-home {
  background: linear-gradient(135deg, rgba(10, 94, 99, 0.1), rgba(242, 143, 59, 0.16));
}

.back-button-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: white;
  font-size: 16px;
  line-height: 1;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  flex-shrink: 0;
}

.back-button-copy {
  display: grid;
  gap: 1px;
  text-align: left;
}

.back-button-copy strong,
.back-button-copy small {
  margin: 0;
}

.back-button-copy small {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.2;
}

@media (max-width: 720px) {
  .back-button {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
