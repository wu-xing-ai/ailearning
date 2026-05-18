<template>
  <div class="progress-container">
    <div class="header">
      <h2>学习进度</h2>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards" v-loading="loading">
      <div class="stat-card">
        <div class="stat-value">{{ formatTime(dashboard.total_time_seconds || 0) }}</div>
        <div class="stat-label">学习时长</div>
      </div>
      <div class="stat-card streak-card">
        <div class="stat-value streak-value">{{ dashboard.streak_days || 0 }}</div>
        <div class="stat-label">连续学习天数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ dashboard.quiz_stats?.answered || 0 }}/{{ dashboard.quiz_stats?.total || 0 }}</div>
        <div class="stat-label">做题练习</div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-actions">
      <router-link to="/ai-knowledge" class="action-btn">去知识交互</router-link>
      <router-link to="/ai-chat" class="action-btn chat-btn">AI对话</router-link>
      <router-link to="/quiz" class="action-btn quiz-btn">做题练习</router-link>
    </div>

    <!-- 空状态引导 -->
    <div v-if="!loading && (!dashboard.total_documents || dashboard.total_documents === 0)" class="empty-guide">
      <div class="guide-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/>
        </svg>
      </div>
      <h3>开始你的学习之旅</h3>
      <p>上传文档、进行AI对话或搜索知识，系统将自动记录你的学习进度</p>
    </div>

    <!-- 学习趋势图 -->
    <div class="section" v-if="dashboard.daily_stats?.length">
      <h3>近7天学习趋势</h3>
      <div class="trend-chart">
        <div class="chart-bars">
          <div v-for="day in dashboard.daily_stats" :key="day.date" class="chart-bar-wrapper">
            <div class="chart-bar-container">
              <div class="chart-bar" :style="{ height: barHeight(day.minutes) + '%' }">
                <span class="bar-tooltip" v-if="day.minutes > 0">{{ day.minutes }}分钟</span>
              </div>
            </div>
            <span class="chart-label">{{ formatDayLabel(day.date) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 文档进度列表 -->
    <div class="section">
      <h3>文档学习进度</h3>
      <el-empty v-if="!dashboard.documents_progress?.length" description="暂无学习记录" />
      <div v-else class="progress-list">
        <div
          v-for="doc in dashboard.documents_progress"
          :key="doc.document_id"
          class="progress-item"
          @click="goToDocument(doc)"
        >
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
    <div class="section" v-if="dashboard.mastery_summary && (dashboard.mastery_summary.high + dashboard.mastery_summary.medium + dashboard.mastery_summary > 0)">
      <h3>知识点掌握分布 <span class="section-subtitle">共 {{ dashboard.total_knowledge_points || 0 }} 个知识点</span></h3>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const dashboard = ref({})

const formatTime = (seconds) => {
  if (!seconds) return '0秒'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}小时${m}分钟`
  if (m > 0) return `${m}分钟${s > 0 ? s + '秒' : ''}`
  return `${s}秒`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const formatDayLabel = (dateStr) => {
  const d = new Date(dateStr)
  const today = new Date()
  if (d.toDateString() === today.toDateString()) return '今天'
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const barHeight = (minutes) => {
  if (!minutes) return 0
  const maxMin = Math.max(...(dashboard.value.daily_stats?.map(d => d.minutes) || [1]), 1)
  return Math.max(5, (minutes / maxMin) * 100)
}

const statusTagType = (s) => ({ completed: 'success', in_progress: 'warning', not_started: 'info' }[s] || 'info')
const statusLabel = (s) => ({ completed: '已完成', in_progress: '学习中', not_started: '未开始' }[s] || s)
const sessionTagType = (t) => ({ reading: '', chat: 'success', knowledge_review: 'warning', search: 'info', quiz: 'danger' }[t] || 'info')
const sessionTypeLabel = (t) => ({ reading: '阅读', chat: '对话', knowledge_review: '复习', search: '检索', quiz: '做题' }[t] || t)

const masteryPercent = (level) => {
  const m = dashboard.value.mastery_summary || {}
  const total = (m.high || 0) + (m.medium || 0) + (m.low || 0)
  if (total === 0) return 33
  return Math.round((m[level] || 0) / total * 100)
}

const goToDocument = (doc) => {
  router.push({ path: '/ai-knowledge', query: { doc_id: doc.document_id } })
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

const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    loadDashboard()
  }
}

// 路由切换时刷新数据（SPA内导航）
watch(() => route.path, (newPath) => {
  if (newPath === '/progress') {
    loadDashboard()
  }
})

onMounted(() => {
  loadDashboard()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
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
  grid-template-columns: repeat(3, 1fr);
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

.streak-card {
  background: linear-gradient(135deg, #FFF9E8 0%, #FFFEF7 100%);
  border-color: rgba(212, 165, 116, 0.2);
}

.streak-value {
  color: #D4A574;
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

.section-subtitle {
  font-size: 13px;
  color: #8B7355;
  font-weight: 400;
  margin-left: 8px;
}

/* 空状态引导 */
.empty-guide {
  background: white;
  border: 2px dashed rgba(212, 165, 116, 0.3);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  margin-bottom: 24px;
}

.guide-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  box-shadow: 0 8px 24px rgba(212, 165, 116, 0.3);
}

.guide-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.empty-guide h3 {
  color: #3D2914;
  font-size: 18px;
  margin: 0 0 8px 0;
  font-family: 'Noto Serif SC', Georgia, serif;
}

.empty-guide p {
  color: #8B7355;
  font-size: 14px;
  margin: 0 0 24px 0;
}

/* 学习趋势图 */
.trend-chart {
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 20px;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 160px;
}

.chart-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.chart-bar-container {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  position: relative;
}

.chart-bar {
  width: 70%;
  max-width: 48px;
  min-height: 4px;
  background: linear-gradient(180deg, #D4A574 0%, #C4956A 100%);
  border-radius: 6px 6px 2px 2px;
  transition: height 0.5s ease;
  position: relative;
}

.chart-bar:hover {
  background: linear-gradient(180deg, #C4956A 0%, #B4855A 100%);
}

.bar-tooltip {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  background: #3D2914;
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.chart-label {
  font-size: 12px;
  color: #8B7355;
  margin-top: 8px;
  text-align: center;
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
  cursor: pointer;
  transition: all 0.2s ease;
}

.progress-item:hover {
  border-color: #D4A574;
  box-shadow: 0 2px 12px rgba(212, 165, 116, 0.15);
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

/* 快捷入口 */
.quick-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.action-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #D4A574 0%, #C4956A 100%);
  color: white;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.25s;
  box-shadow: 0 2px 12px rgba(212, 165, 116, 0.25);
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(212, 165, 116, 0.35);
}

.action-btn.chat-btn {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.25);
}

.action-btn.chat-btn:hover {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.35);
}

.action-btn.quiz-btn {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  box-shadow: 0 2px 12px rgba(103, 194, 58, 0.25);
}

.action-btn.quiz-btn:hover {
  box-shadow: 0 4px 16px rgba(103, 194, 58, 0.35);
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-bars {
    gap: 6px;
    height: 120px;
  }

  .quick-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .action-btn {
    text-align: center;
  }
}
</style>
