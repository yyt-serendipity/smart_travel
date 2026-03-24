<template>
  <div class="file-upload-field">
    <div class="file-upload-toolbar">
      <label class="btn btn-secondary file-upload-button">
        <input class="file-upload-input" type="file" :accept="accept" @change="handleChange" />
        {{ uploading ? "上传中..." : buttonText }}
      </label>
      <button v-if="modelValue" class="chip" type="button" @click="clearValue">清空</button>
    </div>

    <p v-if="helper" class="muted file-upload-helper">{{ helper }}</p>
    <p v-if="selectedName" class="file-upload-name">{{ selectedName }}</p>
    <p v-if="errorMessage" class="file-upload-error">{{ errorMessage }}</p>

    <div v-if="previewMode && modelValue" class="file-upload-preview">
      <img :src="modelValue" :alt="previewAlt" />
    </div>
    <a v-else-if="modelValue" class="file-upload-link" :href="modelValue" target="_blank" rel="noreferrer">
      已上传文件
    </a>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

import { uploadMedia } from "../services/api";


const props = defineProps({
  modelValue: {
    type: String,
    default: "",
  },
  category: {
    type: String,
    default: "attachment",
  },
  accept: {
    type: String,
    default: "image/*",
  },
  helper: {
    type: String,
    default: "",
  },
  previewMode: {
    type: Boolean,
    default: true,
  },
  previewAlt: {
    type: String,
    default: "uploaded",
  },
  buttonLabel: {
    type: String,
    default: "选择文件",
  },
});

const emit = defineEmits(["update:modelValue", "uploaded"]);

const uploading = ref(false);
const errorMessage = ref("");
const selectedName = ref("");

const buttonText = computed(() => (props.modelValue ? "重新上传" : props.buttonLabel));

async function handleChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  selectedName.value = file.name;
  errorMessage.value = "";
  uploading.value = true;

  try {
    const result = await uploadMedia(file, props.category);
    emit("update:modelValue", result.url);
    emit("uploaded", result);
  } catch (error) {
    errorMessage.value = error?.response?.data?.detail || "文件上传失败，请稍后重试。";
  } finally {
    uploading.value = false;
    event.target.value = "";
  }
}

function clearValue() {
  emit("update:modelValue", "");
  selectedName.value = "";
  errorMessage.value = "";
}
</script>
