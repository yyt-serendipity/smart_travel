<template>
  <article class="card hero-carousel">
    <div class="hero-carousel-stage">
      <transition name="fade-slide" mode="out-in">
        <div v-if="activeSlide" :key="activeSlide.key" class="hero-carousel-slide" :style="activeStyle">
          <div class="hero-carousel-overlay">
            <div class="hero-carousel-copy">
              <h1 class="hero-title">{{ activeSlide.title }}</h1>
              <p class="hero-subtitle">{{ activeSlide.description }}</p>

              <div class="chip-row">
                <span v-for="item in activeSlide.meta" :key="item" class="pill hero-carousel-pill">{{ item }}</span>
              </div>
            </div>

            <div class="hero-carousel-footer">
              <RouterLink class="btn btn-primary" :to="activeSlide.to">{{ activeSlide.actionLabel }}</RouterLink>

              <div class="hero-carousel-controls">
                <button class="hero-carousel-arrow" type="button" aria-label="上一张轮播图" @click="prevSlide">←</button>
                <div class="hero-carousel-dots">
                  <button
                    v-for="(slide, index) in slides"
                    :key="slide.key"
                    class="hero-carousel-dot"
                    :class="{ active: index === activeIndex }"
                    type="button"
                    :aria-label="`切换到第 ${index + 1} 张轮播图`"
                    @click="setSlide(index)"
                  ></button>
                </div>
                <button class="hero-carousel-arrow" type="button" aria-label="下一张轮播图" @click="nextSlide">→</button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </article>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";


const props = defineProps({
  slides: {
    type: Array,
    default: () => [],
  },
  intervalMs: {
    type: Number,
    default: 4800,
  },
});

const activeIndex = ref(0);
let timerId = null;

const activeSlide = computed(() => props.slides[activeIndex.value] || null);
const activeStyle = computed(() => ({
  background: activeSlide.value?.image
    ? `linear-gradient(180deg, rgba(8, 28, 36, 0.16), rgba(8, 28, 36, 0.84)), url(${activeSlide.value.image}) center/cover`
    : "linear-gradient(135deg, #0d5c63, #1f7a8c 55%, #f28f3b)",
}));

function setSlide(index) {
  activeIndex.value = index;
  restartTimer();
}

function prevSlide() {
  if (!props.slides.length) return;
  activeIndex.value = (activeIndex.value - 1 + props.slides.length) % props.slides.length;
  restartTimer();
}

function nextSlide() {
  if (!props.slides.length) return;
  activeIndex.value = (activeIndex.value + 1) % props.slides.length;
}

function stopTimer() {
  if (timerId) {
    window.clearInterval(timerId);
    timerId = null;
  }
}

function startTimer() {
  stopTimer();
  if (props.slides.length <= 1) return;
  timerId = window.setInterval(nextSlide, props.intervalMs);
}

function restartTimer() {
  startTimer();
}

watch(
  () => props.slides,
  (slides) => {
    if (!slides.length) {
      activeIndex.value = 0;
      stopTimer();
      return;
    }
    if (activeIndex.value >= slides.length) {
      activeIndex.value = 0;
    }
    startTimer();
  },
  { immediate: true },
);

onMounted(startTimer);
onBeforeUnmount(stopTimer);
</script>

<style scoped>
.hero-carousel {
  overflow: hidden;
  min-height: 520px;
  padding: 0;
}

.hero-carousel-stage,
.hero-carousel-slide {
  min-height: 520px;
}

.hero-carousel-overlay {
  min-height: 520px;
  display: grid;
  align-content: end;
  gap: 28px;
  padding: 38px;
  color: white;
}

.hero-carousel-copy {
  display: grid;
  gap: 18px;
  max-width: 760px;
}

.hero-carousel-overlay .hero-subtitle {
  max-width: 760px;
  color: rgba(255, 255, 255, 0.9);
}

.hero-carousel-pill {
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.14);
}

.hero-carousel-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.hero-carousel-controls,
.hero-carousel-dots {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-carousel-dot,
.hero-carousel-arrow {
  border: 0;
  cursor: pointer;
}

.hero-carousel-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
  transition: width 0.2s ease, background 0.2s ease;
}

.hero-carousel-dot.active {
  width: 30px;
  background: linear-gradient(135deg, #ffffff, #ffd48e);
}

.hero-carousel-arrow {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  color: white;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
}

@media (max-width: 720px) {
  .hero-carousel,
  .hero-carousel-stage,
  .hero-carousel-slide,
  .hero-carousel-overlay {
    min-height: 420px;
  }

  .hero-carousel-overlay {
    padding: 24px;
  }

  .hero-carousel-footer {
    align-items: flex-start;
  }
}
</style>
