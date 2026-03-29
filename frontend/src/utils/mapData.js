function normalizeProvinceName(value) {
  return value?.trim() || "未分省";
}

export function dedupeTags(items = []) {
  const tagSet = new Set();
  items.forEach((item) => {
    (item.tags || []).forEach((tag) => tagSet.add(tag));
  });
  return [...tagSet];
}

export function normalizeProvince(value) {
  return normalizeProvinceName(value);
}
