<template>
  <div class="expandable-text" :class="`expandable-text-${tone}`">
    <p class="muted expandable-text-body" :style="collapsedStyle">
      {{ displayText }}
    </p>
    <button v-if="canExpand" class="expandable-text-toggle" type="button" @click.stop="expanded = !expanded">
      {{ expanded ? collapseLabel : expandLabel }}
    </button>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";


const props = defineProps({
  text: {
    type: String,
    default: "",
  },
  emptyText: {
    type: String,
    default: "暂无介绍",
  },
  lines: {
    type: Number,
    default: 3,
  },
  minLength: {
    type: Number,
    default: 52,
  },
  expandLabel: {
    type: String,
    default: "展开介绍",
  },
  collapseLabel: {
    type: String,
    default: "收起介绍",
  },
  tone: {
    type: String,
    default: "default",
  },
});

const expanded = ref(false);

const displayText = computed(() => {
  const value = String(props.text || "").trim();
  return value || props.emptyText;
});

const canExpand = computed(() => displayText.value.length > props.minLength);
const collapsedStyle = computed(() => {
  if (!canExpand.value || expanded.value) {
    return {};
  }
  return {
    display: "-webkit-box",
    overflow: "hidden",
    WebkitBoxOrient: "vertical",
    WebkitLineClamp: String(props.lines),
  };
});

watch(displayText, () => {
  expanded.value = false;
});
</script>

<style scoped>
.expandable-text {
  display: grid;
  gap: 10px;
}

.expandable-text-body {
  margin: 0;
  line-height: 1.7;
}

.expandable-text-toggle {
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(19, 49, 58, 0.46);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.18s ease;
}

.expandable-text-toggle:hover {
  color: rgba(10, 94, 99, 0.88);
}

.expandable-text-light .expandable-text-body {
  color: rgba(255, 255, 255, 0.9);
}

.expandable-text-light .expandable-text-toggle {
  color: rgba(255, 255, 255, 0.76);
}

.expandable-text-light .expandable-text-toggle:hover {
  color: rgba(255, 255, 255, 0.96);
}
</style>
