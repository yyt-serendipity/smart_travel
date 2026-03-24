<template>
  <transition name="fade-slide">
    <button v-if="visible" class="scroll-top-button" type="button" @click="scrollToTop">
      <span class="scroll-top-icon" aria-hidden="true">↑</span>
      <span class="scroll-top-copy">
        <strong>返回顶部</strong>
        <small>继续浏览当前页面</small>
      </span>
    </button>
  </transition>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";


const route = useRoute();
const visible = ref(false);

function handleScroll() {
  visible.value = window.scrollY > 320;
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onMounted(() => {
  handleScroll();
  window.addEventListener("scroll", handleScroll, { passive: true });
});

watch(
  () => route.fullPath,
  () => {
    handleScroll();
  },
);

onBeforeUnmount(() => {
  window.removeEventListener("scroll", handleScroll);
});
</script>

<style scoped>
.scroll-top-button {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 18;
  min-width: 132px;
  min-height: 58px;
  padding: 10px 16px 10px 10px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  color: white;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  box-shadow: 0 18px 34px rgba(13, 92, 99, 0.24);
  backdrop-filter: blur(10px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.scroll-top-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 38px rgba(13, 92, 99, 0.3);
}

.scroll-top-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 999px;
  font-size: 18px;
  line-height: 1;
  background: rgba(255, 255, 255, 0.16);
}

.scroll-top-copy {
  display: grid;
  gap: 2px;
  text-align: left;
}

.scroll-top-copy strong,
.scroll-top-copy small {
  margin: 0;
}

.scroll-top-copy small {
  font-size: 11px;
  line-height: 1.2;
  color: rgba(255, 255, 255, 0.76);
}

@media (max-width: 720px) {
  .scroll-top-button {
    right: 18px;
    bottom: 18px;
    min-width: 0;
    padding-right: 10px;
  }

  .scroll-top-copy {
    display: none;
  }
}
</style>
