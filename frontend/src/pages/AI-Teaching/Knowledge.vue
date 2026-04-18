<template>
  <div class="knowledge-container">
    <div class="header">
      <h2>知识交互</h2>
      <div class="header-actions">
        <el-select v-model="selectedDocId" placeholder="选择知识库文档" style="width: 260px" @change="onDocChange">
          <el-option v-for="d in documents" :key="d.id" :label="d.filename" :value="d.id" />
        </el-select>
        <el-dropdown split-button type="primary" :loading="processing" :disabled="!selectedDocId" @click="processSelected">
          规则处理
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="aiDialogVisible = true">AI智能处理</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dialog v-model="aiDialogVisible" title="AI智能处理" width="450px">
          <el-form label-width="80px">
            <el-form-item label="AI厂商">
              <el-select v-model="aiProvider" style="width: 100%">
                <el-option label="Ollama (本地)" value="ollama" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="Anthropic" value="anthropic" />
                <el-option label="智谱AI" value="zhipu" />
                <el-option label="通义千问" value="qwen" />
                <el-option label="SiliconFlow" value="siliconflow" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
            <el-form-item label="模型名称">
              <el-input v-model="aiModelName" placeholder="如 qwen2.5" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="aiDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="processing" @click="doAIProcess">开始处理</el-button>
          </template>
        </el-dialog>
      </div>
    </div>

    <div class="knowledge-content">
      <!-- 知识结构树 -->
      <div class="knowledge-tree">
        <div class="tree-header">
          <span class="tree-title">知识结构</span>
          <el-tag v-if="version" type="info" size="small">{{ version }}</el-tag>
        </div>
        <div class="tree-body" v-loading="loading">
          <el-empty v-if="!loading && !outline" description="请选择文档并处理" />

          <template v-else-if="outline">
            <div class="tree-root">
              <div class="root-header" @click="resetSelection">
                <el-icon><Folder /></el-icon>
                <span class="node-name">{{ outline.title }}</span>
              </div>
              <div class="tree-children" v-if="outline.children && outline.children.length">
                <OutlineNode
                  v-for="(child, idx) in outline.children"
                  :key="`${idx}-${child.title}`"
                  :node="child"
                  :parentPath="[]"
                  @select="onSelectNode"
                />
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 知识点与详情 -->
      <div class="knowledge-detail">
        <div class="detail-header">
          <h3>{{ selectedPath.length ? selectedPath.join(' / ') : (outline?.title || '请选择知识点') }}</h3>
          <el-tag v-if="selectedPoints.length" type="warning" size="small">{{ selectedPoints.length }} 个知识点</el-tag>
        </div>

        <div class="detail-body" v-loading="loading">
          <!-- 知识点标签 -->
          <div class="points-section" v-if="selectedPoints.length">
            <div class="section-title">知识点</div>
            <el-scrollbar max-height="280px">
              <div class="points-grid">
                <div
                  v-for="(kp, idx) in selectedPoints"
                  :key="idx"
                  class="point-card"
                  :class="{ active: activePointIdx === idx }"
                  @click="activePointIdx = idx"
                >
                  <el-tag :type="pointTagType(kp.type)" size="small" effect="plain">{{ pointTypeLabel(kp.type) }}</el-tag>
                  <span class="point-text">{{ kp.text }}</span>
                </div>
              </div>
            </el-scrollbar>
          </div>

          <el-empty v-else-if="!loading" description="暂无知识点" />

          <!-- 选中知识点详情 -->
          <div class="point-detail" v-if="activePoint">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>{{ pointTypeLabel(activePoint.type) }}</span>
                  <el-tag size="small" type="info">{{ activePoint.type }}</el-tag>
                </div>
              </template>
              <div class="card-body">
                <p>{{ activePoint.text }}</p>
                <div class="card-meta" v-if="activePoint.node_path?.length">
                  <span>所属章节：{{ activePoint.node_path.join(' / ') }}</span>
                </div>
                <div class="ai-meta" v-if="activePoint.importance || activePoint.summary || activePoint.related_concepts?.length">
                  <div v-if="activePoint.importance" class="meta-row">
                    <span class="meta-label">重要性：</span>
                    <el-rate :model-value="activePoint.importance" disabled size="small" />
                  </div>
                  <div v-if="activePoint.summary" class="meta-row">
                    <span class="meta-label">摘要：</span>
                    <span class="meta-value">{{ activePoint.summary }}</span>
                  </div>
                  <div v-if="activePoint.related_concepts?.length" class="meta-row">
                    <span class="meta-label">相关概念：</span>
                    <el-tag v-for="rc in activePoint.related_concepts" :key="rc" size="small" type="info" style="margin-right: 4px">{{ rc }}</el-tag>
                  </div>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 统计信息 -->
          <div class="detail-footer" v-if="outline">
            <div class="stat">文档: {{ selectedDocName || '-' }}</div>
            <div class="stat">版本: {{ version || '-' }}</div>
            <div class="stat">知识点: {{ knowledgePoints.length }}</div>
            <div class="stat">章节: {{ outline?.children?.length || 0 }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Folder } from '@element-plus/icons-vue'
import api from '@/utils/api'
import OutlineNode from '@/views/OutlineNode.vue'

const route = useRoute()
const router = useRouter()

const documents = ref([])
const selectedDocId = ref('')
const loading = ref(false)
const processing = ref(false)

const outline = ref(null)
const knowledgePoints = ref([])
const version = ref('')
const selectedPath = ref([])
const activePointIdx = ref(-1)
const aiDialogVisible = ref(false)
const aiProvider = ref('ollama')
const aiModelName = ref('')

const selectedDocName = computed(() => {
  return documents.value.find(d => d.id === selectedDocId.value)?.filename || ''
})

const selectedPoints = computed(() => {
  if (!selectedPath.value.length) return knowledgePoints.value
  return knowledgePoints.value.filter(kp => {
    const path = kp.node_path || []
    if (path.length < selectedPath.value.length) return false
    return selectedPath.value.every((p, i) => path[i] === p)
  })
})

const activePoint = computed(() => {
  if (activePointIdx.value < 0 || activePointIdx.value >= selectedPoints.value.length) return null
  return selectedPoints.value[activePointIdx.value]
})

const pointTypeLabel = (type) => {
  const map = { bullet: '要点', trigger: '关键词', summary: '摘要', 'summary-item': '摘要项', sentence: '语句' }
  return map[type] || type
}

const pointTagType = (type) => {
  const map = { bullet: '', trigger: 'danger', summary: 'success', 'summary-item': 'success', sentence: 'info' }
  return map[type] || 'info'
}

const syncRouteDocId = async (docId) => {
  const q = { ...route.query }
  if (docId) q.doc_id = docId
  else delete q.doc_id
  await router.replace({ path: route.path, query: q })
}

const loadDocuments = async () => {
  try {
    documents.value = await api.getDocuments()
    const routeDocId = route.query.doc_id
    if (routeDocId) {
      const matched = documents.value.find(d => d.id === routeDocId)
      if (matched) {
        selectedDocId.value = matched.id
        return
      }
    }
    if (!selectedDocId.value && documents.value.length) {
      const processed = documents.value.find(d => d.processed)
      if (processed) selectedDocId.value = processed.id
    }
  } catch (e) {
    ElMessage.error('加载文档失败: ' + e.message)
  }
}

const loadStructure = async () => {
  if (!selectedDocId.value) {
    outline.value = null
    knowledgePoints.value = []
    version.value = ''
    return
  }
  loading.value = true
  selectedPath.value = []
  activePointIdx.value = -1
  try {
    const res = await api.get(`/api/knowledge/structure?doc_id=${selectedDocId.value}`)
    outline.value = res.outline
    knowledgePoints.value = res.knowledge_points || []
    version.value = res.version
    await syncRouteDocId(selectedDocId.value)
  } catch (e) {
    outline.value = null
    knowledgePoints.value = []
    version.value = ''
    ElMessage.warning(e.message)
  } finally {
    loading.value = false
  }
}

const onDocChange = async () => {
  await loadStructure()
}

const processSelected = async () => {
  if (!selectedDocId.value) return
  processing.value = true
  try {
    await api.post(`/api/knowledge/process?doc_id=${selectedDocId.value}`)
    ElMessage.success('规则处理完成')
    await loadStructure()
  } catch (e) {
    ElMessage.error('处理失败: ' + e.message)
  } finally {
    processing.value = false
  }
}

const doAIProcess = async () => {
  if (!selectedDocId.value) return
  processing.value = true
  try {
    await api.processKnowledgeAI(selectedDocId.value, aiProvider.value, aiModelName.value, true)
    ElMessage.success('AI智能处理完成')
    aiDialogVisible.value = false
    await loadStructure()
  } catch (e) {
    ElMessage.error('AI处理失败: ' + e.message)
  } finally {
    processing.value = false
  }
}

const onSelectNode = (path) => {
  selectedPath.value = path
  activePointIdx.value = -1
}

const resetSelection = () => {
  selectedPath.value = []
  activePointIdx.value = -1
}

watch(() => route.query.doc_id, async (docId) => {
  if (!docId || !documents.value.length || docId === selectedDocId.value) return
  const matched = documents.value.find(d => d.id === docId)
  if (matched) {
    selectedDocId.value = matched.id
    await loadStructure()
  }
})

watch(selectedPoints, () => {
  activePointIdx.value = -1
})

onMounted(async () => {
  await loadDocuments()
  if (selectedDocId.value) {
    await loadStructure()
  }
})
</script>

<style scoped>
.knowledge-container {
  padding: 24px;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(139, 90, 43, 0.08);
  min-height: calc(100vh - 140px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.knowledge-content {
  display: flex;
  gap: 24px;
}

/* 左侧知识树 */
.knowledge-tree {
  width: 340px;
  min-width: 340px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
  display: flex;
  flex-direction: column;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
}

.tree-title {
  font-size: 16px;
  font-weight: 600;
  color: #3D2914;
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
}

.tree-body {
  flex: 1;
  max-height: 500px;
  overflow-y: auto;
}

.tree-root {
  margin-bottom: 8px;
}

.root-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #5D4E37;
  font-weight: 600;
}

.root-header:hover {
  background: rgba(212, 165, 116, 0.1);
}

.root-header :deep(.el-icon) {
  color: #D4A574;
  margin-right: 8px;
}

.node-name {
  font-size: 14px;
}

.tree-children {
  margin-left: 24px;
  padding-left: 12px;
  border-left: 2px solid rgba(212, 165, 116, 0.2);
}

/* 右侧详情 */
.knowledge-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
}

.detail-header h3 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-size: 18px;
  margin: 0;
}

.detail-body {
  flex: 1;
}

/* 知识点网格 */
.points-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #3D2914;
  margin-bottom: 12px;
}

.points-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.point-card {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid rgba(139, 90, 43, 0.12);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  max-width: 300px;
  background: #FFFEF7;
}

.point-card:hover {
  border-color: #D4A574;
  box-shadow: 0 2px 8px rgba(212, 165, 116, 0.15);
}

.point-card.active {
  border-color: #D4A574;
  background: rgba(212, 165, 116, 0.08);
}

.point-text {
  font-size: 13px;
  color: #5D4E37;
  line-height: 1.5;
}

/* 知识点详情卡片 */
.point-detail {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  color: #3D2914;
}

.card-body p {
  color: #5D4E37;
  line-height: 1.8;
  margin: 0 0 12px 0;
}

.card-meta {
  font-size: 12px;
  color: #8B7355;
  padding-top: 8px;
  border-top: 1px solid rgba(139, 90, 43, 0.08);
}

/* 统计信息 */
.detail-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(139, 90, 43, 0.1);
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #8B7355;
}

.stat {
  padding: 6px 0;
}

/* 卡片样式 */
:deep(.el-card) {
  border-radius: 12px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF5E6 100%);
  border-bottom: 1px solid rgba(139, 90, 43, 0.1);
}

/* Select 下拉框样式 */
.header-actions :deep(.el-input__wrapper) {
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.15);
}

.header-actions :deep(.el-input__wrapper:hover) {
  border-color: #D4A574;
}

/* AI增强元数据 */
.ai-meta {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(139, 90, 43, 0.08);
}

.meta-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: #8B7355;
  min-width: 60px;
}

.meta-value {
  font-size: 12px;
  color: #5D4E37;
  font-style: italic;
}
</style>
