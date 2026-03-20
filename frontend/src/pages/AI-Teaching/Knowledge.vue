<template>
  <div class="knowledge-container">
    <div class="header">
      <h2>知识交互</h2>
      <div class="header-actions">
        <el-select v-model="selectedTopic" placeholder="选择知识点">
          <el-option
            v-for="item in topics"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-button type="primary" @click="searchKnowledge">搜索</el-button>
      </div>
    </div>

    <div class="knowledge-content">
      <div class="knowledge-tree">
        <el-tree
          :data="knowledgeData"
          :props="defaultProps"
          default-expand-all
          @node-click="handleNodeClick"
        />
      </div>

      <div class="knowledge-detail">
        <div class="detail-header">
          <h3>{{ selectedNode?.label || '请选择知识点' }}</h3>
          <el-tag>知识点 {{ selectedNode?.level || 0 }}</el-tag>
        </div>

        <div class="detail-content">
          <div v-if="selectedNode">
            <el-card class="box-card">
              <template #header>
                <div class="card-header">
                  <span>知识内容</span>
                  <el-button text @click="expandContent">展开全部</el-button>
                </div>
                <div class="content-preview">
                  {{ selectedNode.content || '该知识点暂无详细内容' }}
                </div>
              </template>
              <div class="card-footer">
                <el-button-group>
                  <el-button size="small" @click="addToFavorites">收藏</el-button>
                  <el-button size="small" @click="shareKnowledge">分享</el-button>
                  <el-button size="small">编辑</el-button>
                </el-button-group>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElTree } from 'element-plus'

const selectedTopic = ref('')
const selectedNode = ref(null)

const topics = ref([
  { value: 'math', label: '数学' },
  { value: 'english', label: '英语' },
  { value: 'physics', label: '物理' },
  { value: 'chemistry', label: '化学' }
])

const knowledgeData = ref([
  {
    id: 1,
    label: '代数基础',
    level: 1,
    content: '代数是数学的一个分支，主要研究数和字母的运算、方程和不等式的性质等内容...'
  },
  {
    id: 2,
    label: '几何',
    level: 1,
    content: '几何是研究空间形状、大小和性质的数学分支...'
  },
  {
    id: 11,
    label: '线性代数',
    level: 2,
    content: '线性代数是代数学的一个分支，主要研究向量空间和线性映射等内容...'
  },
  {
    id: 12,
    label: '解析几何',
    level: 2,
    content: '解析几何是结合代数方法和几何概念来研究几何问题的数学分支...'
  },
  {
    id: 21,
    label: '平面几何',
    level: 2,
    content: '平面几何研究平面上图形的性质、关系和度量...'
  }
])

const defaultProps = {
  children: 'children',
  label: 'label'
}

const handleNodeClick = (data) => {
  selectedNode.value = data
}

const searchKnowledge = () => {
  ElMessage.info(`搜索知识点: ${selectedTopic.value}`)
}

const expandContent = () => {
  ElMessage.info('展开完整内容')
}

const addToFavorites = () => {
  ElMessage.success('已添加到收藏夹')
}

const shareKnowledge = () => {
  ElMessage.info('分享功能')
}
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
  height: 500px;
}

.knowledge-tree {
  width: 300px;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 12px;
  padding: 16px;
  background: white;
  box-shadow: 0 2px 12px rgba(139, 90, 43, 0.05);
}

.knowledge-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h3 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-size: 18px;
  margin: 0;
}

.card-header {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 12px;
  color: #3D2914;
}

.content-preview {
  color: #5D4E37;
  line-height: 1.8;
  max-height: 300px;
  overflow-y: auto;
}

.card-footer {
  margin-top: 16px;
  text-align: right;
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

/* 按钮组样式 */
:deep(.el-button-group .el-button) {
  border-color: rgba(139, 90, 43, 0.2);
  color: #5D4E37;
}

:deep(.el-button-group .el-button:hover) {
  background: rgba(212, 165, 116, 0.1);
  border-color: #D4A574;
  color: #D4A574;
}

/* 树形组件样式 */
:deep(.el-tree-node__content:hover) {
  background-color: rgba(212, 165, 116, 0.1);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(212, 165, 116, 0.15);
}

/* Select 下拉框样式 */
.header-actions :deep(.el-input__wrapper) {
  background: #FFFEF7;
  border: 1px solid rgba(139, 90, 43, 0.15);
}

.header-actions :deep(.el-input__wrapper:hover) {
  border-color: #D4A574;
}
</style>