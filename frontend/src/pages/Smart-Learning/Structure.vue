<template>
  <div class="structure-container">
    <div class="header">
      <h2>知识结构化</h2>
      <div class="header-actions">
        <el-button type="primary" @click="startStructureProcess">开始结构化</el-button>
        <el-button @click="resetStructure">重置</el-button>
      </div>
    </div>

    <div class="structure-content">
      <!-- 知识结构展示区域 -->
      <div class="knowledge-tree">
        <div class="tree-header">
          <span class="tree-title">知识结构</span>
          <el-tag type="info">基于文档内容自动生成</el-tag>
        </div>

        <div class="tree-content">
          <div class="tree-node" v-for="node in knowledgeStructure" :key="node.id">
            <div class="node-header">
              <el-icon><folder /></el-icon>
              <span class="node-name">{{ node.name }}</span>
            </div>
            <div class="node-content" v-if="node.children">
              <div class="tree-node" v-for="child in node.children" :key="child.id">
                <div class="node-header">
                  <el-icon><document /></el-icon>
                  <span class="node-name">{{ child.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 结构化进度 -->
      <div class="structure-progress">
        <h3>结构化进度</h3>
        <el-progress :percentage="progressPercentage" :format="formatProgress" />
        <div class="progress-details">
          <div>已处理文档: {{ processedDocuments }} / {{ totalDocuments }}</div>
          <div>知识点数量: {{ knowledgePoints }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElProgress } from 'element-plus'
import { Folder, Document } from '@element-plus/icons-vue'

const knowledgeStructure = ref([
  {
    id: 1,
    name: '数学学科',
    children: [
      { id: 11, name: '代数基础' },
      { id: 12, name: '几何' },
      { id: 13, name: '概率统计' }
    ]
  },
  {
    id: 2,
    name: '英语学科',
    children: [
      { id: 21, name: '语法' },
      { id: 22, name: '词汇' },
      { id: 23, name: '阅读理解' }
    ]
  },
  {
    id: 3,
    name: '物理学科',
    children: [
      { id: 31, name: '力学' },
      { id: 32, name: '热学' },
      { id: 33, name: '电磁学' }
    ]
  }
])

const progressPercentage = ref(65)
const processedDocuments = ref(3)
const totalDocuments = ref(5)
const knowledgePoints = ref(42)

const startStructureProcess = async () => {
  ElMessage.info('开始知识结构化处理...')

  // 模拟处理过程
  for (let i = 0; i <= 100; i += 10) {
    await new Promise(resolve => setTimeout(resolve, 200))
    progressPercentage.value = i
  }

  ElMessage.success('知识结构化完成！')
}

const resetStructure = () => {
  ElMessage.info('重置知识结构')
  progressPercentage.value = 0
}

const formatProgress = (percentage) => {
  return `${percentage}%`
}
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
</style>