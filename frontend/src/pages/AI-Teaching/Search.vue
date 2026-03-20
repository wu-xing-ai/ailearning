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
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  min-height: calc(100vh - 120px);
}

.search-header {
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  max-width: 600px;
  margin-top: 15px;
}

.search-results {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.results-content {
  min-height: 200px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-item {
  padding: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  transition: all 0.3s;
  cursor: pointer;
}

.result-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.result-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.result-snippet {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 10px 0;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

:deep(.highlight) {
  background-color: #fff3cd;
  color: #856404;
  padding: 0 2px;
  border-radius: 2px;
}
</style>