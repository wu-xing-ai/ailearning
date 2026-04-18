<template>
  <div class="progress-container">
    <div class="header">
      <h2>学习进度</h2>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards" v-loading="loading">
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.total_documents || 0 }}</div>
        <div class="stat-label">学习文档</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.completed_documents || 0 }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatTime(dashboard.total_time_seconds || 0) }}</div>
        <div class="stat-label">学习时长</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ (dashboard.mastery_summary?.high || 0) }}</div>
        <div class="stat-label">已掌握知识点</div>
      </div>
    </div>

    <!-- 文档进度列表 -->
    <div class="section">
      <h3>文档学习进度</h3>
      <el-empty v-if="!dashboard.documents_progress?.length" description="暂无学习记录" />
      <div v-else class="progress-list">
        <div v-for="doc in dashboard.documents_progress" :key="doc.document_id" class="progress-item">
          <div class="progress-item-header">
            <span class="doc-name">{{ doc.filename }}</span>
            <el-tag :type="statusTagType(doc.status)" size="small">{{ statusLabel(doc.status) }}</el-tag>
          </div>
          <el-progress :percentage="Math.round(doc.progress_percent)" :stroke-width="10" />
          <div class="progress-meta">
            <span>学习时长: {{ formatTime(doc.time_spent_seconds) }}</span>
            <span v-if="doc.last_accessed_at">最后访问: {{ formatDate(doc.last_accessed_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 掌握度分布 -->
    <div class="section" v-if="dashboard.mastery_summary">
      <h3>知识点掌握分布</h3>
      <div class="mastery-bar">
        <div class="mastery-segment high" :style="{width: masteryPercent('high') + '%'}">
          {{ dashboard.mastery_summary.high || 0 }} 熟练
        </div>
        <div class="mastery-segment medium" :style="{width: masteryPercent('medium') + '%'}">
          {{ dashboard.mastery_summary.medium || 0 }} 了解
        </div>
        <div class="mastery-segment low" :style="{width: masteryPercent('low') + '%'}">
          {{ dashboard.mastery_summary.low || 0 }} 未学
        </div>
      </div>
    </div>

    <!-- 最近学习记录 -->
    <div class="section" v-if="dashboard.recent_sessions?.length">
      <h3>最近学习记录</h3>
      <div class="session-list">
        <div v-for="s in dashboard.recent_sessions" :key="s.id" class="session-item">
          <el-tag :type="sessionTagType(s.session_type)" size="small">{{ sessionTypeLabel(s.session_type) }}</el-tag>
          <span class="session-time">{{ formatDate(s.started_at) }}</span>
          <span class="session-duration">{{ formatTime(s.duration_seconds) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const loading = ref(false)
const dashboard = ref({})

const formatTime = (seconds) => {
  if (!seconds) return '0分钟'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const statusTagType = (s) => ({ completed: 'success', in_progress: 'warning', not_started: 'info' }[s] || 'info')
const statusLabel = (s) => ({ completed: '已完成', in_progress: '学习中', not_started: '未开始' }[s] || s)
const sessionTagType = (t) => ({ reading: '', chat: 'success', knowledge_review: 'warning', search: 'info' }[t] || 'info')
const sessionTypeLabel = (t) => ({ reading: '阅读', chat: '对话', knowledge_review: '复习', search: '检索' }[t] || t)

const masteryPercent = (level) => {
  const m = dashboard.value.mastery_summary || {}
  const total = (m.high || 0) + (m.medium || 0) + (m.low || 0)
  if (total === 0) return 33
  return Math.round((m[level] || 0) / total * 100)
}

const loadDashboard = async () => {
  loading.value = true
  try {
    dashboard.value = await api.get('/api/progress/dashboard')
  } catch (e) {
    ElMessage.error('加载进度失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.progress-container {
  padding: 24px;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(139, 90, 43, 0.08);
  min-height: calc(100vh - 140px);
}

.header h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-weight: 600;
  margin: 0 0 24px 0;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.04);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #3D2914;
  font-family: 'Noto Serif SC', Georgia, serif;
}

.stat-label {
  font-size: 13px;
  color: #8B7355;
  margin-top: 4px;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  font-family: 'Noto Serif SC', Georgia, serif;
  color: #3D2914;
  font-size: 16px;
  margin: 0 0 16px 0;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-item {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.progress-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.doc-name {
  font-weight: 600;
  color: #3D2914;
  font-size: 14px;
}

.progress-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #8B7355;
  margin-top: 8px;
}

.mastery-bar {
  display: flex;
  height: 36px;
  border-radius: 18px;
  overflow: hidden;
  background: #f5f0e8;
}

.mastery-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: white;
  min-width: 60px;
  transition: width 0.3s ease;
}

.mastery-segment.high { background: linear-gradient(135deg, #67c23a, #529b2e); }
.mastery-segment.medium { background: linear-gradient(135deg, #e6a23c, #cf8e24); }
.mastery-segment.low { background: linear-gradient(135deg, #909399, #73767a); }

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.08);
  border-radius: 8px;
  font-size: 13px;
  color: #5D4E37;
}

.session-time { flex: 1; }
.session-duration { color: #8B7355; }

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #D4A574 0%, #C4956A 100%);
}
</style>
