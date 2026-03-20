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
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.structure-content {
  display: flex;
  gap: 20px;
}

.knowledge-tree {
  flex: 1;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.tree-title {
  font-size: 16px;
  font-weight: bold;
}

.tree-content {
  max-height: 400px;
  overflow-y: auto;
}

.tree-node {
  margin-bottom: 10px;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.node-header:hover {
  background: #f5f7fa;
}

.node-name {
  margin-left: 8px;
  font-size: 14px;
}

.structure-progress {
  width: 300px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: #fafafa;
}

.progress-details {
  margin-top: 15px;
  font-size: 12px;
  color: #666;
}
</style>