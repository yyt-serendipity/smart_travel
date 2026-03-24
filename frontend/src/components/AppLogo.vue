<template>
  <div class="app-logo" :class="{ inverse, compact }">
    <span class="app-logo-mark" aria-hidden="true">
      <svg viewBox="0 0 64 64" role="img">
        <circle cx="32" cy="32" r="19" class="logo-ring" />
        <path class="logo-route" d="M18 44c8-10 16-14 28-24" />
        <circle cx="46" cy="20" r="3" class="logo-point" />
        <path class="logo-needle logo-needle-main" d="M32 12 38 32 32 52 26 32Z" />
        <path class="logo-needle logo-needle-side" d="M20 32 32 26 44 32 32 38Z" />
        <circle cx="32" cy="32" r="4.5" class="logo-core" />
      </svg>
    </span>

    <span v-if="showText" class="app-logo-copy">
      <strong>{{ title }}</strong>
      <small v-if="subtitle">{{ subtitle }}</small>
    </span>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: "China Travel Compass",
  },
  subtitle: {
    type: String,
    default: "",
  },
  inverse: {
    type: Boolean,
    default: false,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  showText: {
    type: Boolean,
    default: true,
  },
});
</script>

<style scoped>
.app-logo {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  color: var(--text);
}

.app-logo.compact {
  gap: 12px;
}

.app-logo.inverse {
  color: white;
}

.app-logo-mark {
  display: inline-grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  background:
    radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.24), transparent 36%),
    linear-gradient(145deg, #0d5c63, #1b4965 58%, #f28f3b 120%);
  box-shadow: 0 16px 28px rgba(13, 92, 99, 0.22);
}

.app-logo.inverse .app-logo-mark {
  background:
    radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.2), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.08));
  box-shadow: 0 16px 28px rgba(6, 22, 28, 0.24);
}

.app-logo-mark svg {
  width: 34px;
  height: 34px;
}

.logo-ring,
.logo-route,
.logo-needle,
.logo-point,
.logo-core {
  vector-effect: non-scaling-stroke;
}

.logo-ring {
  fill: none;
  stroke: rgba(255, 255, 255, 0.8);
  stroke-width: 2.2;
}

.logo-route {
  fill: none;
  stroke: rgba(255, 255, 255, 0.68);
  stroke-linecap: round;
  stroke-width: 2.6;
  stroke-dasharray: 2 4;
}

.logo-point,
.logo-core {
  fill: #ffd48e;
}

.logo-needle-main {
  fill: rgba(255, 255, 255, 0.96);
}

.logo-needle-side {
  fill: rgba(255, 255, 255, 0.48);
}

.app-logo-copy {
  display: grid;
  min-width: 0;
}

.app-logo-copy strong,
.app-logo-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-logo-copy strong {
  font-size: 15px;
  letter-spacing: 0.01em;
}

.app-logo-copy small {
  margin-top: 3px;
  color: var(--muted);
  font-size: 12px;
}

.app-logo.inverse .app-logo-copy small {
  color: rgba(255, 255, 255, 0.72);
}
</style>
