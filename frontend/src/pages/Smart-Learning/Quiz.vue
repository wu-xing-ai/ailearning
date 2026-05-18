<template>
  <div class="quiz-page">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">做题练习</h1>
      <p class="page-desc">通过练习巩固知识点，检验学习效果</p>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-select v-model="selectedDocId" placeholder="选择文档" class="doc-select" @change="loadQuizzes">
        <el-option
          v-for="doc in documents"
          :key="doc.id"
          :label="doc.filename"
          :value="doc.id"
        >
          <span>{{ doc.filename }}</span>
          <span class="doc-stats" v-if="quizDocMap[doc.id]">
            {{ quizDocMap[doc.id].answered }}/{{ quizDocMap[doc.id].total_questions }}题
          </span>
          <span class="doc-stats" v-else style="color: #bbb;">未出题</span>
        </el-option>
      </el-select>

      <el-button
        type="primary"
        :loading="generating"
        @click="handleGenerate"
        :disabled="!selectedDocId"
      >
        {{ generating ? '生成中...' : '生成题目' }}
      </el-button>
    </div>

    <!-- 统计栏 -->
    <div class="stats-bar" v-if="quizzes.length > 0">
      <div class="stat-item">
        <span class="stat-label">已答</span>
        <span class="stat-value">{{ stats.answered }}/{{ stats.total }}题</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">正确率</span>
        <span class="stat-value" :class="stats.accuracy >= 60 ? 'text-success' : 'text-danger'">
          {{ stats.accuracy }}%
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">正确</span>
        <span class="stat-value text-success">{{ stats.correct }}题</span>
      </div>
    </div>

    <!-- 无已处理文档 -->
    <div class="empty-state" v-if="documents.length === 0 && !loading">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"/>
        </svg>
      </div>
      <h3>暂无已处理文档</h3>
      <p>请先前往「知识交互」页面，对文档进行AI智能处理，系统会自动根据知识点生成练习题</p>
      <el-button type="primary" @click="$router.push('/ai-knowledge')">前往知识交互</el-button>
    </div>

    <!-- 无选中文档题目为空 -->
    <div class="empty-state" v-else-if="selectedDocId && quizzes.length === 0 && !loading">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
        </svg>
      </div>
      <h3>该文档暂无题目</h3>
      <p>点击上方「生成题目」按钮手动生成，或对该文档进行AI智能处理</p>
    </div>

    <!-- 题目列表 -->
    <div class="quiz-list" v-if="quizzes.length > 0">
      <div
        v-for="(quiz, index) in quizzes"
        :key="quiz.id"
        class="quiz-card"
        :class="{
          'card-correct': quiz.attempt && quiz.attempt.is_correct,
          'card-wrong': quiz.attempt && !quiz.attempt.is_correct
        }"
      >
        <div class="quiz-header">
          <span class="quiz-number">第{{ index + 1 }}题</span>
          <el-tag
            :type="difficultyType(quiz.difficulty)"
            size="small"
            effect="plain"
          >{{ difficultyLabel(quiz.difficulty) }}</el-tag>
        </div>

        <div class="quiz-question">{{ quiz.question_text }}</div>

        <el-radio-group
          :model-value="quiz.attempt ? quiz.attempt.selected_index : (answers[quiz.id] ?? null)"
          @change="val => handleSelect(quiz.id, val)"
          :disabled="!!quiz.attempt"
          class="options-group"
        >
          <div
            v-for="(opt, oi) in quiz.options"
            :key="oi"
            class="option-item"
            :class="{
              'option-selected': answers[quiz.id] === oi,
              'option-correct': quiz.attempt && oi === quiz.correct_index,
              'option-wrong': quiz.attempt && oi === quiz.attempt.selected_index && !quiz.attempt.is_correct,
            }"
          >
            <el-radio :value="oi">
              <span class="option-label">{{ optionLabels[oi] }}.</span>
              {{ opt }}
            </el-radio>
          </div>
        </el-radio-group>

        <!-- 提交按钮 -->
        <div class="quiz-actions" v-if="!quiz.attempt && answers[quiz.id] !== undefined">
          <el-button
            type="primary"
            size="small"
            :loading="submitting[quiz.id]"
            @click="handleSubmit(quiz)"
          >提交答案</el-button>
        </div>

        <!-- 已答结果 -->
        <div class="quiz-result" v-if="quiz.attempt">
          <div class="result-badge" :class="quiz.attempt.is_correct ? 'badge-correct' : 'badge-wrong'">
            {{ quiz.attempt.is_correct ? '回答正确' : '回答错误' }}
          </div>
          <div class="result-explanation" v-if="quiz.explanation">
            <strong>解析：</strong>{{ quiz.explanation }}
          </div>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div class="loading-state" v-if="loading">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import api from '@/utils/api'

const documents = ref([])
const quizDocMap = ref({}) // document_id -> { answered, total_questions, correct }
const selectedDocId = ref('')
const quizzes = ref([])
const stats = ref({ total: 0, answered: 0, correct: 0, accuracy: 0 })
const loading = ref(false)
const generating = ref(false)
const answers = reactive({})
const submitting = reactive({})
const optionLabels = ['A', 'B', 'C', 'D']
let quizSessionId = null

onMounted(async () => {
  await loadDocuments()
  // Start study session for quiz activity
  try {
    const res = await api.startStudySession(null, 'quiz')
    quizSessionId = res.session_id
  } catch (e) { /* ignore */ }
})

// End session on page leave
onBeforeUnmount(() => {
  if (quizSessionId) {
    api.beaconEndStudySession(quizSessionId)
    quizSessionId = null
  }
})

async function loadDocuments() {
  loading.value = true
  try {
    // Load all documents + quiz-enabled documents in parallel
    const [allDocs, quizDocs] = await Promise.all([
      api.getDocuments(),
      api.getQuizDocuments().catch(() => []),
    ])
    // Build quiz stats map
    const qMap = {}
    for (const qd of quizDocs) {
      qMap[qd.document_id] = qd
    }
    quizDocMap.value = qMap

    // Show all processed documents
    documents.value = allDocs.filter(d => d.processed)
    // Auto-select first doc with quizzes, or first doc
    if (documents.value.length > 0 && !selectedDocId.value) {
      const firstQuizDoc = documents.value.find(d => qMap[d.id])
      selectedDocId.value = firstQuizDoc ? firstQuizDoc.id : documents.value[0].id
      await loadQuizzes()
    }
  } catch (e) {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function loadQuizzes() {
  if (!selectedDocId.value) return
  loading.value = true
  try {
    const [quizData, statsData] = await Promise.all([
      api.getDocumentQuizzes(selectedDocId.value),
      api.getQuizStats(selectedDocId.value),
    ])
    quizzes.value = quizData
    stats.value = statsData
    // Clear local answers
    Object.keys(answers).forEach(k => delete answers[k])
  } catch (e) {
    ElMessage.error('加载题目失败')
  } finally {
    loading.value = false
  }
}

function handleSelect(quizId, val) {
  answers[quizId] = val
}

async function handleSubmit(quiz) {
  const selected = answers[quiz.id]
  if (selected === undefined) return
  submitting[quiz.id] = true
  try {
    const result = await api.submitQuizAnswer(quiz.id, selected)
    if (result.already_answered) {
      ElMessage.info('已经答过该题')
    } else if (result.is_correct) {
      ElMessage.success('回答正确！')
    } else {
      ElMessage.warning('回答错误')
    }
    // Reload to reflect changes
    await loadQuizzes()
    // Refresh quiz doc stats
    const quizDocs = await api.getQuizDocuments().catch(() => [])
    const qMap = {}
    for (const qd of quizDocs) qMap[qd.document_id] = qd
    quizDocMap.value = qMap
  } catch (e) {
    ElMessage.error('提交失败')
  } finally {
    submitting[quiz.id] = false
  }
}

async function handleGenerate() {
  if (!selectedDocId.value) return
  generating.value = true
  try {
    const result = await api.generateQuizzes(selectedDocId.value)
    ElMessage.success(`成功生成 ${result.count} 道题目`)
    await loadQuizzes()
    const quizDocs = await api.getQuizDocuments().catch(() => [])
    const qMap = {}
    for (const qd of quizDocs) qMap[qd.document_id] = qd
    quizDocMap.value = qMap
  } catch (e) {
    ElMessage.error(e.message || '生成题目失败')
  } finally {
    generating.value = false
  }
}

function difficultyType(d) {
  const map = { easy: 'success', medium: 'warning', hard: 'danger' }
  return map[d] || 'info'
}

function difficultyLabel(d) {
  const map = { easy: '简单', medium: '中等', hard: '困难' }
  return map[d] || '中等'
}
</script>

<style scoped>
.quiz-page {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #3D2914;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 14px;
  color: #8B7355;
  margin: 0;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: center;
}

.doc-select {
  flex: 1;
}

.doc-stats {
  float: right;
  color: #8B7355;
  font-size: 12px;
}

.stats-bar {
  display: flex;
  gap: 24px;
  background: #FFF9E8;
  border: 1px solid #E8DCC8;
  border-radius: 12px;
  padding: 16px 24px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #8B7355;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #3D2914;
}

.text-success { color: #4CAF50; }
.text-danger { color: #F44336; }

.quiz-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quiz-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #E8DCC8;
  transition: border-color 0.2s;
}

.quiz-card.card-correct {
  border-color: #4CAF50;
  background: #F0FFF0;
}

.quiz-card.card-wrong {
  border-color: #F44336;
  background: #FFF5F5;
}

.quiz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.quiz-number {
  font-size: 14px;
  font-weight: 600;
  color: #5D4037;
}

.quiz-question {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  line-height: 1.6;
  margin-bottom: 16px;
}

.options-group {
  width: 100%;
}

.option-item {
  margin-bottom: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #E8DCC8;
  transition: all 0.2s;
}

.option-item:hover {
  border-color: #D4A574;
}

.option-item.option-selected {
  border-color: #D4A574;
  background: #FFF9E8;
}

.option-item.option-correct {
  border-color: #4CAF50;
  background: #E8F5E9;
}

.option-item.option-wrong {
  border-color: #F44336;
  background: #FFEBEE;
}

.option-label {
  font-weight: 600;
  margin-right: 4px;
}

.quiz-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.quiz-result {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #E8DCC8;
}

.result-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}

.badge-correct {
  background: #E8F5E9;
  color: #2E7D32;
}

.badge-wrong {
  background: #FFEBEE;
  color: #C62828;
}

.result-explanation {
  font-size: 14px;
  color: #5D4037;
  line-height: 1.6;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  color: #D4A574;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h3 {
  font-size: 18px;
  color: #3D2914;
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: #8B7355;
  margin: 0 0 20px;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #8B7355;
}

@media (max-width: 768px) {
  .quiz-page {
    padding: 0 4px;
  }

  .stats-bar {
    gap: 16px;
    padding: 12px 16px;
    flex-wrap: wrap;
  }

  .stat-value {
    font-size: 16px;
  }

  .toolbar {
    flex-direction: column;
  }

  .doc-select {
    width: 100%;
  }

  .quiz-card {
    padding: 16px;
  }
}
</style>
