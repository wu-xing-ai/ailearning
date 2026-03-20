<template>
  <div class="search-container">
    <div class="search-header">
      <h2>智能检索</h2>
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="输入关键词搜索知识..."
          :prefix-icon="Search"
          @keyup.enter="performSearch"
          clearable
        />
        <el-button type="primary" @click="performSearch" :loading="searching">搜索</el-button>
      </div>
    </div>

    <div class="search-results">
      <div class="results-header">
        <span v-if="hasSearched">找到 {{ searchResults.length }} 个结果</span>
        <span v-else>输入关键词搜索知识库中的文档</span>
        <el-radio-group v-model="sortBy" size="small" @change="sortResults">
          <el-radio-button label="relevance">相关性</el-radio-button>
          <el-radio-button label="time">时间</el-radio-button>
          <el-radio-button label="type">类型</el-radio-button>
        </el-radio-group>
      </div>

      <div class="results-content" v-loading="searching">
        <el-empty v-if="hasSearched && searchResults.length === 0" description="未找到相关结果" />

        <div class="result-list">
          <div class="result-item" v-for="result in searchResults" :key="result.id">
            <div class="result-main">
              <div class="result-header">
                <h3 class="result-title">{{ result.filename }}</h3>
                <el-tag size="small" type="info">{{ result.file_type }}</el-tag>
              </div>
              <p class="result-snippet" v-html="highlightKeyword(result.snippet)"></p>
              <div class="result-footer">
                <span class="result-status">
                  <el-tag :type="result.processed ? 'success' : 'warning'" size="small">
                    {{ result.processed ? '已处理' : '待处理' }}
                  </el-tag>
                </span>
                <span class="result-time">{{ formatDateTime(result.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/utils/api'

const searchQuery = ref('')
const sortBy = ref('relevance')
const searching = ref(false)
const hasSearched = ref(false)
const searchResults = ref([])

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 高亮关键词
const highlightKeyword = (text) => {
  if (!text || !searchQuery.value) return text
  const keyword = searchQuery.value.trim()
  if (!keyword) return text

  const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi')
  return text.replace(regex, '<mark class="highlight">$1</mark>')
}

// 转义正则特殊字符
const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 执行搜索
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  hasSearched.value = true

  try {
    const response = await fetch(`/api/documents/search?q=${encodeURIComponent(searchQuery.value.trim())}`)
    const results = await response.json()
    searchResults.value = results

    if (results.length > 0) {
      ElMessage.success(`找到 ${results.length} 个相关结果`)
    } else {
      ElMessage.info('未找到相关结果')
    }
  } catch (error) {
    ElMessage.error('搜索失败: ' + error.message)
  } finally {
    searching.value = false
  }
}

// 排序结果
const sortResults = () => {
  if (searchResults.value.length === 0) return

  const results = [...searchResults.value]

  switch (sortBy.value) {
    case 'time':
      results.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      break
    case 'type':
      results.sort((a, b) => (a.file_type || '').localeCompare(b.file_type || ''))
      break
    default:
      // 相关性 - 保持原顺序
      break
  }

  searchResults.value = results
}
</script>

<style scoped>
.search-container {
  padding: 24px;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(139, 90, 43, 0.08);
  min-height: calc(100vh - 140px);
}

.search-header {
  margin-bottom: 24px;
}

.search-header h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-weight: 600;
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  gap: 12px;
  max-width: 600px;
}

.search-box :deep(.el-input__wrapper) {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.15);
  border-radius: 10px;
  box-shadow: none;
  transition: all 0.25s ease;
}

.search-box :deep(.el-input__wrapper:hover) {
  border-color: #D4A574;
}

.search-box :deep(.el-input__wrapper.is-focus) {
  border-color: #D4A574;
  box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.15);
}

.search-results {
  margin-top: 24px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
  color: #8B7355;
  font-size: 14px;
}

.results-content {
  min-height: 200px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  padding: 20px;
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.04);
}

.result-item:hover {
  border-color: #D4A574;
  box-shadow: 0 4px 16px rgba(212, 165, 116, 0.15);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.result-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #3D2914;
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
}

.result-snippet {
  color: #5D4E37;
  font-size: 14px;
  line-height: 1.7;
  margin: 0 0 12px 0;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #8B7355;
}

/* 高亮关键词 */
:deep(.highlight) {
  background-color: rgba(212, 165, 116, 0.3);
  color: #8B5A2B;
  padding: 1px 4px;
  border-radius: 3px;
}

/* Radio 按钮组样式 */
:deep(.el-radio-button__inner) {
  border-color: rgba(139, 90, 43, 0.2);
  color: #5D4E37;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border-color: #D4A574;
  box-shadow: -1px 0 0 0 #D4A574;
}

/* Tag 标签样式 */
:deep(.el-tag--info) {
  background-color: rgba(139, 90, 43, 0.08);
  border-color: rgba(139, 90, 43, 0.15);
  color: #8B7355;
}
</style>