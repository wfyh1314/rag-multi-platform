<script setup>
import { computed, onMounted, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useTagDictionary } from '@/views/tag/composables/useTagDictionary'

const {
  categories,
  loading,
  error,
  loadCategories,
  addCategory,
  renameCategory,
  removeCategory,
  addTag,
  editTag,
  removeTag,
} = useTagDictionary()

const activeNames = ref([])
const categoryDialogVisible = ref(false)
const categoryDialogMode = ref('create')
const categoryForm = ref({ id: '', name: '' })

const tagDialogVisible = ref(false)
const tagDialogMode = ref('create')
const tagForm = ref({ id: '', categoryId: '', name: '', keywords: '' })

const categoryDialogTitle = computed(() =>
  categoryDialogMode.value === 'create' ? '新增分类' : '编辑分类'
)
const tagDialogTitle = computed(() => (tagDialogMode.value === 'create' ? '新增标签' : '编辑标签'))

onMounted(() => {
  loadCategories()
})

function openCreateCategory() {
  categoryDialogMode.value = 'create'
  categoryForm.value = { id: '', name: '' }
  categoryDialogVisible.value = true
}

function openEditCategory(category) {
  categoryDialogMode.value = 'edit'
  categoryForm.value = { id: category.id, name: category.name }
  categoryDialogVisible.value = true
}

async function submitCategory() {
  const name = categoryForm.value.name.trim()
  if (!name) return
  if (categoryDialogMode.value === 'create') {
    await addCategory(name)
  } else {
    await renameCategory(categoryForm.value.id, name)
  }
  categoryDialogVisible.value = false
}

function openCreateTag(category) {
  tagDialogMode.value = 'create'
  tagForm.value = { id: '', categoryId: category.id, name: '', keywords: '' }
  tagDialogVisible.value = true
}

function openEditTag(tag) {
  tagDialogMode.value = 'edit'
  tagForm.value = {
    id: tag.id,
    categoryId: tag.category_id,
    name: tag.name,
    keywords: tag.keywords || '',
  }
  tagDialogVisible.value = true
}

async function submitTag() {
  const name = tagForm.value.name.trim()
  if (!name) return
  const payload = { name, keywords: tagForm.value.keywords.trim() }
  if (tagDialogMode.value === 'create') {
    await addTag(tagForm.value.categoryId, payload)
  } else {
    await editTag(tagForm.value.id, payload)
  }
  tagDialogVisible.value = false
}

defineExpose({ loadCategories, categories })
</script>

<template>
  <section class="page-card tag-dictionary-panel">
    <div class="tag-panel-header">
      <h2 class="page-card-title">标签字典</h2>
      <el-button type="primary" size="small" @click="openCreateCategory">
        <el-icon><Plus /></el-icon>
        新增
      </el-button>
    </div>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      class="tag-alert"
    />

    <div v-loading="loading" class="tag-dictionary-body">
      <el-empty v-if="!loading && !categories.length" description="暂无分类，请先新增" />

      <el-collapse v-else v-model="activeNames" class="tag-category-collapse">
        <el-collapse-item
          v-for="category in categories"
          :key="category.id"
          :name="category.id"
        >
          <template #title>
            <div class="tag-category-title">
              <span class="tag-category-name">{{ category.name }}</span>
              <el-badge :value="category.tag_count" class="tag-category-badge" />
            </div>
          </template>

          <div class="tag-category-actions">
            <el-button link type="primary" @click.stop="openCreateTag(category)">
              <el-icon><Plus /></el-icon>
              添加标签
            </el-button>
            <el-button link type="primary" @click.stop="openEditCategory(category)">编辑</el-button>
            <el-button link type="danger" @click.stop="removeCategory(category)">删除</el-button>
          </div>

          <div v-if="category.tags?.length" class="tag-item-list">
            <div v-for="tag in category.tags" :key="tag.id" class="tag-item-row">
              <div class="tag-item-main">
                <span class="tag-item-name">{{ tag.name }}</span>
                <span v-if="tag.keywords" class="tag-item-keywords">{{ tag.keywords }}</span>
              </div>
              <div class="tag-item-actions">
                <el-button link type="primary" @click="openEditTag(tag)">编辑</el-button>
                <el-button link type="danger" @click="removeTag(tag)">删除</el-button>
              </div>
            </div>
          </div>
          <p v-else class="tag-empty-tip">该分类下暂无标签</p>
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-dialog v-model="categoryDialogVisible" :title="categoryDialogTitle" width="420px">
      <el-form label-width="80px" @submit.prevent="submitCategory">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" maxlength="128" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCategory">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="tagDialogVisible" :title="tagDialogTitle" width="480px">
      <el-form label-width="80px" @submit.prevent="submitTag">
        <el-form-item label="标签名称">
          <el-input v-model="tagForm.name" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="tagForm.keywords"
            type="textarea"
            :rows="3"
            placeholder="多个关键词用逗号分隔，用于自动匹配文档内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tagDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTag">确定</el-button>
      </template>
    </el-dialog>
  </section>
</template>
