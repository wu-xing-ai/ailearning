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
      <div class="search-mode">
        <el-segmented v-model="searchMode" :options="searchModeOptions" size="default" />
      </div>
    </div>

    <div class="search-results">
      <div class="results-header">
        <span v-if="hasSearched">找到 {{ searchResults.length }} 个结果 ({{ searchModeLabel }})</span>
        <span v-else>输入关键词搜索知识库中的文档</span>
      </div>

      <div class="results-content" v-loading="searching">
        <el-empty v-if="hasSearched && searchResults.length === 0" description="未找到相关结果" />

        <div class="result-list">
          <div class="result-item" v-for="(result, idx) in searchResults" :key="idx">
            <div class="result-main">
              <div class="result-header">
                <h3 class="result-title">{{ result.filename || '文档' }}</h3>
                <el-tag size="small" type="info">{{ result.file_type || 'txt' }}</el-tag>
                <el-tag v-if="result.source" size="small" :type="sourceTagType(result.source)">
                  {{ sourceLabel(result.source) }}
                </el-tag>
              </div>
              <p class="result-snippet" v-html="highlightKeyword(result.snippet || result.text)"></p>
              <div class="result-footer">
                <div class="result-meta">
                  <span v-if="result.score" class="result-score">
                    相似度: {{ (result.score * 100).toFixed(1) }}%
                    <el-progress :percentage="Math.round(result.score * 100)" :show-text="false" :stroke-width="6" style="width: 80px; margin-left: 4px" />
                  </span>
                  <span v-if="result.chunk_index !== undefined" class="result-chunk">分块 #{{ result.chunk_index }}</span>
                </div>
                <span class="result-status">
                  <el-tag v-if="result.processed !== undefined" :type="result.processed ? 'success' : 'warning'" size="small">
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
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/utils/api'

const searchQuery = ref('')
const searchMode = ref('keyword')
const searching = ref(false)
const hasSearched = ref(false)
const searchResults = ref([])

const searchModeOptions = [
  { label: '关键词', value: 'keyword' },
  { label: '混合搜索', value: 'hybrid' },
  { label: '语义', value: 'semantic' },
]

const searchModeLabel = computed(() => {
  const map = { hybrid: '混合搜索', keyword: '关键词搜索', semantic: '语义搜索' }
  return map[searchMode.value] || searchMode.value
})

const sourceTagType = (source) => {
  const map = { keyword: 'warning', semantic: 'success', hybrid: '' }
  return map[source] || 'info'
}

const sourceLabel = (source) => {
  const map = { keyword: '关键词', semantic: '语义', hybrid: '混合' }
  return map[source] || source
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const highlightKeyword = (text) => {
  if (!text || !searchQuery.value) return text || ''
  const keyword = searchQuery.value.trim()
  if (!keyword) return text
  const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi')
  return text.replace(regex, '<mark class="highlight">$1</mark>')
}

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  hasSearched.value = true

  try {
    if (searchMode.value === 'keyword') {
      const response = await fetch(`/api/documents/search?q=${encodeURIComponent(searchQuery.value.trim())}`)
      searchResults.value = await response.json()
    } else {
      const result = await api.semanticSearch(searchQuery.value.trim(), searchMode.value)
      searchResults.value = result.results || []
    }

    if (searchResults.value.length > 0) {
      ElMessage.success(`找到 ${searchResults.value.length} 个相关结果`)
    } else {
      ElMessage.info('未找到相关结果')
    }
  } catch (error) {
    ElMessage.error('搜索失败: ' + error.message)
  } finally {
    searching.value = false
  }
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

.search-mode {
  margin-top: 12px;
}

.search-mode :deep(.el-segmented) {
  background: rgba(139, 90, 43, 0.06);
}

.search-mode :deep(.el-segmented__item-selected) {
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  color: white;
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

.result-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.result-score {
  display: flex;
  align-items: center;
  color: #D4A574;
  font-weight: 500;
}

.result-chunk {
  color: #8B7355;
}

/* 高亮关键词 */
:deep(.highlight) {
  background-color: rgba(212, 165, 116, 0.3);
  color: #8B5A2B;
  padding: 1px 4px;
  border-radius: 3px;
}

/* Tag 标签样式 */
:deep(.el-tag--info) {
  background-color: rgba(139, 90, 43, 0.08);
  border-color: rgba(139, 90, 43, 0.15);
  color: #8B7355;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #D4A574 0%, #C4956A 100%);
}
</style>
