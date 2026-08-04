<script setup>
import { computed, ref } from 'vue'
import TagDictionaryPanel from '@/views/tag/components/TagDictionaryPanel.vue'
import DocumentTagsPanel from '@/views/tag/components/DocumentTagsPanel.vue'

const dictionaryRef = ref(null)
const documentRef = ref(null)

const tagOptions = computed(() => {
  const raw = dictionaryRef.value?.categories
  const categories = raw?.value ?? raw ?? []
  return categories.flatMap((category) =>
    (category.tags || []).map((tag) => ({
      ...tag,
      category_name: category.name,
      label: `${category.name}: ${tag.name}`,
    }))
  )
})
</script>

<template>
  <div class="tag-manage-page">
    <header class="page-header">
      <h1 class="page-header-title">标签管理</h1>
      <p class="page-header-subtitle">
        维护标签字典，切分时自动匹配关键词为文档打标签
      </p>
    </header>

    <div class="tag-manage-layout">
      <TagDictionaryPanel ref="dictionaryRef" />
      <DocumentTagsPanel ref="documentRef" :tag-options="tagOptions" />
    </div>
  </div>
</template>
