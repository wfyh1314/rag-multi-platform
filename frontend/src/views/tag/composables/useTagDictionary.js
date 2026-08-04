import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchTagCategories,
  createTagCategory,
  updateTagCategory,
  deleteTagCategory,
  createTag,
  updateTag,
  deleteTag,
} from '@/views/tag/api/tag'

export function useTagDictionary() {
  const categories = ref([])
  const loading = ref(false)
  const error = ref('')

  async function loadCategories() {
    loading.value = true
    error.value = ''
    try {
      const data = await fetchTagCategories()
      categories.value = data.categories || []
    } catch (err) {
      error.value = err.message || '加载标签字典失败'
      categories.value = []
    } finally {
      loading.value = false
    }
  }

  async function addCategory(name) {
    await createTagCategory(name)
    ElMessage.success('分类已创建')
    await loadCategories()
  }

  async function renameCategory(categoryId, name) {
    await updateTagCategory(categoryId, name)
    ElMessage.success('分类已更新')
    await loadCategories()
  }

  async function removeCategory(category) {
    await ElMessageBox.confirm(`确定删除分类「${category.name}」及其下所有标签？`, '删除确认', {
      type: 'warning',
    })
    await deleteTagCategory(category.id)
    ElMessage.success('分类已删除')
    await loadCategories()
  }

  async function addTag(categoryId, payload) {
    await createTag(categoryId, payload)
    ElMessage.success('标签已创建')
    await loadCategories()
  }

  async function editTag(tagId, payload) {
    await updateTag(tagId, payload)
    ElMessage.success('标签已更新')
    await loadCategories()
  }

  async function removeTag(tag) {
    await ElMessageBox.confirm(`确定删除标签「${tag.name}」？`, '删除确认', {
      type: 'warning',
    })
    await deleteTag(tag.id)
    ElMessage.success('标签已删除')
    await loadCategories()
  }

  const flatTags = () =>
    categories.value.flatMap((category) =>
      (category.tags || []).map((tag) => ({
        ...tag,
        category_name: category.name,
        label: `${category.name}: ${tag.name}`,
      }))
    )

  return {
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
    flatTags,
  }
}
