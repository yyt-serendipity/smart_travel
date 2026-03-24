<template>
  <article class="card auth-showcase" :class="`auth-showcase-${variant}`">
    <div class="auth-showcase-grid">
      <div class="auth-showcase-copy">
        <span class="eyebrow">{{ eyebrow }}</span>
        <h1 class="hero-title auth-showcase-title">{{ title }}</h1>
        <p class="hero-subtitle">{{ description }}</p>

        <div class="chip-row" style="margin-top: 16px">
          <span v-for="item in highlights" :key="item" class="pill auth-pill">{{ item }}</span>
        </div>

        <div class="auth-metric-grid">
          <div v-for="metric in metrics" :key="metric.label" class="mini-spot auth-metric-card">
            <strong>{{ metric.value }}</strong>
            <p class="muted">{{ metric.label }}</p>
          </div>
        </div>
      </div>

      <div class="auth-showcase-visual">
        <div class="auth-light auth-light-a"></div>
        <div class="auth-light auth-light-b"></div>

        <div class="auth-floating-card auth-floating-card-left">
          <strong>城市与景点联动</strong>
          <p>从城市推荐直接进入景点级路线规划。</p>
        </div>

        <div class="auth-floating-card auth-floating-card-right">
          <strong>社区内容沉淀</strong>
          <p>发帖、点赞、评论和个人主页保持一条线索。</p>
        </div>

        <div class="auth-preview-frame">
          <img class="auth-preview-image" src="/auth-showcase.png" alt="登录注册页设计参考图" />
        </div>

        <div class="auth-orbit">
          <span v-for="item in floatingNotes" :key="item" class="auth-orbit-pill">{{ item }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: "Travel Access",
  },
  variant: {
    type: String,
    default: "login",
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: "",
  },
  highlights: {
    type: Array,
    default: () => [],
  },
  metrics: {
    type: Array,
    default: () => [],
  },
  floatingNotes: {
    type: Array,
    default: () => [],
  },
});
</script>

<style scoped>
.auth-showcase {
  overflow: hidden;
  min-height: 100%;
  padding: 34px;
  background:
    radial-gradient(circle at top left, rgba(242, 143, 59, 0.18), transparent 28%),
    radial-gradient(circle at right, rgba(31, 122, 140, 0.22), transparent 32%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(235, 245, 247, 0.96));
}

.auth-showcase-login {
  background:
    radial-gradient(circle at top left, rgba(242, 143, 59, 0.18), transparent 28%),
    radial-gradient(circle at right, rgba(31, 122, 140, 0.22), transparent 32%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(235, 245, 247, 0.96));
}

.auth-showcase-register {
  background:
    radial-gradient(circle at top left, rgba(13, 92, 99, 0.18), transparent 28%),
    radial-gradient(circle at right, rgba(242, 143, 59, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(247, 251, 250, 0.94), rgba(241, 245, 251, 0.96));
}

.auth-showcase-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(360px, 1.08fr);
  gap: 28px;
  align-items: center;
  min-height: 100%;
}

.auth-showcase-copy {
  display: grid;
  gap: 16px;
}

.auth-showcase-title {
  max-width: 11ch;
}

.auth-pill {
  color: var(--primary);
  background: rgba(13, 92, 99, 0.08);
}

.auth-metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.auth-metric-card {
  position: relative;
  display: grid;
  gap: 10px;
  min-height: 112px;
  padding: 20px 22px;
  border-radius: 24px;
  border: 1px solid rgba(10, 94, 99, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(242, 248, 248, 0.84));
  box-shadow: 0 16px 34px rgba(24, 52, 61, 0.08);
  align-content: center;
  overflow: hidden;
}

.auth-metric-card::after {
  content: "";
  position: absolute;
  inset: auto -26px -34px auto;
  width: 108px;
  height: 108px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(10, 94, 99, 0.1), transparent 66%);
}

.auth-metric-card:last-child {
  grid-column: 1 / -1;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 18px;
}

.auth-metric-card strong {
  position: relative;
  z-index: 1;
  font-size: 28px;
  font-family: var(--heading-font);
  line-height: 1;
}

.auth-metric-card p {
  margin: 0;
  position: relative;
  z-index: 1;
  max-width: 8em;
  line-height: 1.5;
}

.auth-metric-card:last-child p {
  max-width: none;
}

.auth-showcase-visual {
  position: relative;
  min-height: 520px;
  display: grid;
  place-items: center;
}

.auth-preview-frame {
  position: relative;
  width: min(100%, 640px);
  padding: 14px;
  border-radius: 34px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 28px 62px rgba(24, 52, 61, 0.16);
  animation: previewFloat 7s ease-in-out infinite;
  z-index: 2;
}

.auth-preview-image {
  width: 100%;
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(24, 52, 61, 0.1);
}

.auth-floating-card {
  position: absolute;
  width: 200px;
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border: 1px solid rgba(13, 92, 99, 0.08);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 34px rgba(13, 92, 99, 0.1);
  backdrop-filter: blur(14px);
  z-index: 3;
}

.auth-floating-card p,
.auth-floating-card strong {
  margin: 0;
}

.auth-floating-card-left {
  left: -12px;
  top: 32px;
  animation: noteFloat 5.5s ease-in-out infinite;
}

.auth-floating-card-right {
  right: 8px;
  bottom: 56px;
  animation: noteFloat 6.5s ease-in-out infinite reverse;
}

.auth-orbit {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-orbit-pill {
  position: absolute;
  min-width: 112px;
  padding: 10px 20px;
  border-radius: 999px;
  color: white;
  background: linear-gradient(135deg, rgba(13, 92, 99, 0.94), rgba(31, 122, 140, 0.9));
  box-shadow: 0 14px 28px rgba(13, 92, 99, 0.16);
  animation: orbitFloat 8s ease-in-out infinite;
  text-align: center;
}

.auth-orbit-pill:nth-child(1) {
  top: 12%;
  right: 18%;
}

.auth-orbit-pill:nth-child(2) {
  left: 6%;
  bottom: 18%;
  animation-delay: 1.2s;
}

.auth-orbit-pill:nth-child(3) {
  right: 10%;
  top: 48%;
  animation-delay: 2.4s;
}

.auth-light {
  position: absolute;
  border-radius: 999px;
  filter: blur(12px);
}

.auth-light-a {
  width: 150px;
  height: 150px;
  left: 22px;
  top: 50px;
  background: rgba(242, 143, 59, 0.18);
}

.auth-light-b {
  width: 180px;
  height: 180px;
  right: 22px;
  bottom: 28px;
  background: rgba(31, 122, 140, 0.18);
}

@keyframes previewFloat {
  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-10px);
  }
}

@keyframes noteFloat {
  0%,
  100% {
    transform: translateY(0px);
  }

  50% {
    transform: translateY(-14px);
  }
}

@keyframes orbitFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }

  50% {
    transform: translate3d(0, -12px, 0);
  }
}

@media (max-width: 1180px) {
  .auth-showcase-grid {
    grid-template-columns: 1fr;
  }

  .auth-showcase-title {
    max-width: none;
  }
}

@media (max-width: 720px) {
  .auth-showcase {
    padding: 24px;
  }

  .auth-metric-grid {
    grid-template-columns: 1fr;
  }

  .auth-metric-card:last-child {
    grid-column: auto;
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .auth-showcase-visual {
    min-height: 360px;
  }

  .auth-floating-card {
    display: none;
  }

  .auth-orbit-pill {
    font-size: 12px;
  }
}
</style>
