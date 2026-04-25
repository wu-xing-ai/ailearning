<template>
  <div class="structure-container">
    <div class="header">
      <h2>知识结构化</h2>
      <div class="header-actions">
        <el-select v-model="selectedDocId" placeholder="选择文档" style="width: 240px" @change="onDocChange">
          <el-option v-for="d in documents" :key="d.id" :label="d.filename" :value="d.id" />
        </el-select>
        <el-dropdown split-button type="primary" :loading="processing" :disabled="!selectedDocId" @click="processSelected">
          规则处理
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="processAISelected">AI智能处理</el-dropdown-item>
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
        <el-button @click="resetStructure">重置</el-button>
      </div>
    </div>

    <div class="structure-content">
      <!-- 知识结构展示区域 -->
      <div class="knowledge-tree">
        <div class="tree-header">
          <span class="tree-title">知识结构</span>
          <el-tag type="info">基于文档内容自动生成</el-tag>
          <el-tag v-if="structureSource === 'ai'" type="success" style="margin-left: 8px">AI处理 {{ aiModelLabel }}</el-tag>
        </div>

        <div class="tree-content" v-loading="loading">
          <el-alert v-if="selectedDocError" type="error" :closable="false" show-icon style="margin-bottom: 12px">
            {{ selectedDocError }}
          </el-alert>
          <el-empty v-if="!loading && !outline && !selectedDocError" description="请选择文档并处理" />

          <template v-else-if="outline">
            <div class="tree-node">
              <div class="node-header">
                <el-icon><folder /></el-icon>
                <span class="node-name">{{ outline.title }}</span>
              </div>
              <div class="node-content" v-if="outline.children && outline.children.length">
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

      <!-- 知识点 -->
      <div class="structure-progress">
        <h3>知识点</h3>
        <div v-if="selectedPoints.length === 0" style="color: #8B7355; font-size: 13px">暂无知识点</div>
        <el-scrollbar v-else height="420px">
          <div
            v-for="(kp, idx) in selectedPoints"
            :key="idx"
            class="knowledge-point-card"
          >
            <div class="kp-text" v-html="renderLatexText(kp.text)"></div>
            <div class="kp-meta" v-if="kp.importance || kp.summary || kp.related_concepts?.length">
              <el-rate v-if="kp.importance" :model-value="kp.importance" disabled size="small" style="margin-right: 8px" />
              <span v-if="kp.summary" class="kp-summary">{{ kp.summary }}</span>
              <el-tag v-for="rc in (kp.related_concepts || []).slice(0, 3)" :key="rc" size="small" type="info" style="margin-left: 4px">{{ rc }}</el-tag>
            </div>
            <el-tag v-else type="warning" size="small" style="margin-top: 4px">{{ kp.type }}</el-tag>
          </div>
        </el-scrollbar>

        <div class="progress-details" style="margin-top: 16px">
          <div>文档: {{ selectedDocName || '-' }}</div>
          <div>版本: {{ version || '-' }}</div>
          <div>知识点数量: {{ knowledgePoints.length }}</div>
          <div>当前节点: {{ selectedPath.join(' / ') || '全部' }}</div>
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
import { renderLatexText } from '@/utils/latex'
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
const structureSource = ref('')
const aiModelLabel = ref('')

const selectedPath = ref([])
const aiDialogVisible = ref(false)
const aiProvider = ref('ollama')
const aiModelName = ref('')

const selectedDocName = computed(() => {
  const d = documents.value.find(x => x.id === selectedDocId.value)
  return d?.filename || ''
})

const selectedDocError = computed(() => {
  const d = documents.value.find(x => x.id === selectedDocId.value)
  return d?.content_error || ''
})

const selectedPoints = computed(() => {
  if (selectedPath.value.length === 0) return knowledgePoints.value
  return knowledgePoints.value.filter(kp => {
    const path = kp.node_path || []
    if (path.length < selectedPath.value.length) return false
    return selectedPath.value.every((p, i) => path[i] === p)
  })
})

const syncRouteDocId = async (docId) => {
  const nextQuery = { ...route.query }
  if (docId) {
    nextQuery.doc_id = docId
  } else {
    delete nextQuery.doc_id
  }
  await router.replace({ path: route.path, query: nextQuery })
}

const handleMissingSelectedDocument = async () => {
  selectedDocId.value = ''
  outline.value = null
  knowledgePoints.value = []
  version.value = ''
  selectedPath.value = []
  await syncRouteDocId('')
}

const loadDocuments = async () => {
  try {
    documents.value = await api.getDocuments()
    const routeDocId = route.query.doc_id
    if (routeDocId) {
      const matched = documents.value.find(doc => doc.id === routeDocId)
      if (matched) {
        selectedDocId.value = matched.id
        return
      }
      ElMessage.warning('路由中的文档不存在或已删除')
      await handleMissingSelectedDocument()
      return
    }

    if (selectedDocId.value) {
      const stillExists = documents.value.find(doc => doc.id === selectedDocId.value)
      if (!stillExists) {
        ElMessage.info('当前查看的文档已被删除')
        await handleMissingSelectedDocument()
      }
    }

    if (!selectedDocId.value && documents.value.length > 0) {
      const processedDoc = documents.value.find(doc => doc.processed)
      if (processedDoc) {
        selectedDocId.value = processedDoc.id
      }
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
  try {
    const res = await api.get(`/api/knowledge/structure?doc_id=${selectedDocId.value}`)
    outline.value = res.outline
    knowledgePoints.value = res.knowledge_points || []
    version.value = res.version
    structureSource.value = res.source || 'rule'
    aiModelLabel.value = res.ai_model || ''
    await syncRouteDocId(selectedDocId.value)
    if (!res.outline?.children?.length && !res.knowledge_points?.length) {
      ElMessage.info('当前文档已处理，但暂未生成大纲或知识点')
    }
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

const processAISelected = () => {
  aiDialogVisible.value = true
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

const resetStructure = () => {
  selectedPath.value = []
}

const onSelectNode = (path) => {
  selectedPath.value = path
}

watch(() => route.query.doc_id, async (docId) => {
  if (!docId || !documents.value.length || docId === selectedDocId.value) return
  const matched = documents.value.find(doc => doc.id === docId)
  if (matched) {
    selectedDocId.value = matched.id
    await loadStructure()
  }
})

onMounted(async () => {
  await loadDocuments()
  if (selectedDocId.value) {
    await loadStructure()
  }
})
</script>

<style scoped>
.structure-container {
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

.structure-content {
  display: flex;
  gap: 24px;
}

.knowledge-tree {
  flex: 1;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
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

.tree-content {
  max-height: 400px;
  overflow-y: auto;
}

.tree-node {
  margin-bottom: 8px;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #5D4E37;
}

.node-header:hover {
  background: rgba(212, 165, 116, 0.1);
}

.node-header :deep(.el-icon) {
  color: #D4A574;
  margin-right: 8px;
}

.node-name {
  font-size: 14px;
}

.node-content {
  margin-left: 24px;
  padding-left: 12px;
  border-left: 2px solid rgba(212, 165, 116, 0.2);
}

.structure-progress {
  width: 300px;
  padding: 20px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
}

.structure-progress h3 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-size: 16px;
  margin: 0 0 16px 0;
}

.progress-details {
  margin-top: 16px;
  font-size: 13px;
  color: #8B7355;
}

.progress-details > div {
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 90, 43, 0.08);
}

.progress-details > div:last-child {
  border-bottom: none;
}

/* 进度条颜色 */
:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #D4A574 0%, #C4956A 100%);
}

.knowledge-point-card {
  padding: 8px 12px;
  margin-bottom: 8px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 8px;
  background: rgba(255, 249, 232, 0.5);
  transition: all 0.2s ease;
}

.knowledge-point-card:hover {
  border-color: rgba(212, 165, 116, 0.3);
  box-shadow: 0 2px 8px rgba(139, 90, 43, 0.08);
}

.kp-text {
  font-size: 13px;
  color: #3D2914;
  line-height: 1.5;
}

.kp-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 6px;
  gap: 4px;
}

.kp-summary {
  font-size: 12px;
  color: #8B7355;
  font-style: italic;
}
</style>