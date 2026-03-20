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
        />
        <el-button type="primary" @click="performSearch">搜索</el-button>
        <el-button @click="advancedSearch">高级搜索</el-button>
      </div>
    </div>

    <div class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 个结果</span>
        <el-radio-group v-model="sortBy" size="small">
          <el-radio-button label="relevance">相关性</el-radio-button>
          <el-radio-button label="time">时间</el-radio-button>
          <el-radio-button label="type">类型</el-radio-button>
        </el-radio-group>
      </div>

      <div class="results-content">
        <el-row :gutter="20">
          <el-col :span="8" v-for="result in searchResults" :key="result.id">
            <el-card :body-style="{ padding: '0' }" shadow="hover" class="result-card">
              <img :src="result.image" class="card-image" />
              <div class="card-content">
                <h3 class="card-title">{{ result.title }}</h3>
                <p class="card-description">{{ result.description }}</p>
                <div class="card-footer">
                  <span class="card-type">{{ result.type }}</span>
                  <span class="card-time">{{ result.updateTime }}</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElCard, ElRow, ElCol } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const searchQuery = ref('')
const sortBy = ref('relevance')
const searchResults = ref([
  {
    id: 1,
    title: '二次方程解法',
    description: '详细介绍了二次方程的几种解法，包括公式法、因式分解法等',
    type: '数学',
    updateTime: '2024-01-15 14:30',
    image: 'https://picsum.photos/200/120'
  },
  {
    id: 2,
    title: '英语过去式规则',
    description: '英语时态学习：过去式的构成规则和用法详解',
    type: '英语',
    updateTime: '2024-01-16 09:15',
    image: 'https://picsum.photos/200/120'
  },
  {
    id: 3,
    title: '牛顿运动定律',
    description: '物理学基础：牛顿三大运动定律的详细解析',
    type: '物理',
    updateTime: '2024-01-17 16:45',
    image: 'https://picsum.photos/200/120'
  }
])

const performSearch = () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  ElMessage.info(`搜索: ${searchQuery.value}`)

  // 模拟搜索结果
  ElMessage.success(`找到 ${searchResults.value.length} 个相关结果`)
}

const advancedSearch = () => {
  ElMessage.info('高级搜索功能')
}

const formatResultType = (type) => {
  const typeMap = {
    '数学': { color: 'primary', icon: ' yuan' },
    '英语': { color: 'success', icon: ' document' },
    '物理': { color: 'warning', icon: ' lightbulb' }
  }
  return typeMap[type] || { color: 'info', icon: ' document' }
}
</script>

<style scoped>
.search-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.search-header {
  margin-bottom: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  max-width: 600px;
}

.search-results {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.result-card {
  transition: all 0.3s;
}

.result-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.card-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.card-content {
  padding: 15px;
}

.card-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: bold;
}

.card-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
}

.card-type {
  background: #f0f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 12px;
}
</style>