<template>
  <div class="library-container">
    <div class="header">
      <h2>知识库管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showUploadDialog = true">上传文档</el-button>
        <el-button @click="refreshLibrary" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="document-list">
      <el-table :data="documents" style="width: 100%" v-loading="loading">
        <el-table-column prop="filename" label="文件名" width="250"></el-table-column>
        <el-table-column prop="file_type" label="类型" width="100"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.content_error" type="danger">异常</el-tag>
            <el-tag v-else :type="row.processed ? 'success' : 'warning'">
              {{ row.processed ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180"></el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" :loading="processingDocId === row.id" @click="processDocument(row.id)">处理</el-button>
            <el-button size="small" :disabled="!row.processed" @click="viewStructure(row.id)">查看结构</el-button>
            <el-button size="small" type="danger" :loading="deletingDocId === row.id" @click="confirmDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && documents.length === 0" description="暂无文档，请上传" />
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="500">
      <el-upload
        ref="uploadRef"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        :limit="10"
        accept=".pdf,.docx,.txt,.xlsx,.md"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOCX、TXT、XLSX、MD 格式
          </div>
        </template>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="uploadDocuments" :loading="uploading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const router = useRouter()
const documents = ref([])
const showUploadDialog = ref(false)
const fileList = ref([])
const loading = ref(false)
const uploading = ref(false)
const processingDocId = ref('')
const deletingDocId = ref('')

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

// 加载文档列表
const loadDocuments = async () => {
  loading.value = true
  try {
    const result = await api.getDocuments()
    documents.value = result.map(doc => ({
      ...doc,
      created_at: formatDateTime(doc.created_at)
    }))
  } catch (error) {
    ElMessage.error('加载文档列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 刷新知识库
const refreshLibrary = async () => {
  await loadDocuments()
  ElMessage.success('刷新成功')
}

// 处理文档
const processDocument = async (docId) => {
  processingDocId.value = docId
  try {
    await api.post(`/api/knowledge/process?doc_id=${docId}`)
    ElMessage.success('文档处理完成，正在跳转结构化页面')
    await loadDocuments()
    await router.push({ path: '/smart-structure', query: { doc_id: docId } })
  } catch (error) {
    ElMessage.error('处理失败: ' + error.message)
  } finally {
    processingDocId.value = ''
  }
}

const viewStructure = async (docId) => {
  await router.push({ path: '/smart-structure', query: { doc_id: docId } })
}

// 确认删除
const confirmDelete = async (docId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteDocument(docId)
  } catch {
    // 用户取消
  }
}

// 删除文档
const deleteDocument = async (docId) => {
  deletingDocId.value = docId
  try {
    await api.deleteDocument(docId)
    documents.value = documents.value.filter(doc => doc.id !== docId)
    ElMessage.success('删除成功，列表已更新')
  } catch (error) {
    ElMessage.error('删除失败: ' + error.message)
  } finally {
    deletingDocId.value = ''
  }
}

// 文件选择变化
const handleFileChange = (file, files) => {
  fileList.value = files
}

// 文件移除
const handleFileRemove = (file, files) => {
  fileList.value = files
}

// 上传文档
const uploadDocuments = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    const results = await api.uploadDocuments(fileList.value)

    const successCount = results.filter(r => r.success).length
    const failCount = results.filter(r => !r.success).length

    if (successCount > 0) {
      ElMessage.success(`成功上传 ${successCount} 个文件`)
    }
    if (failCount > 0) {
      const failedFiles = results.filter(r => !r.success).map(r => r.filename).join(', ')
      ElMessage.warning(`${failCount} 个文件上传失败: ${failedFiles}`)
    }

    showUploadDialog.value = false
    fileList.value = []
    await loadDocuments()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.library-container {
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
}

.header .actions {
  display: flex;
  gap: 12px;
}

.document-list {
  margin-top: 20px;
}

/* 表格样式 */
.document-list :deep(.el-table) {
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
}

.document-list :deep(.el-table th.el-table__cell) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF5E6 100%);
  color: #3D2914;
  font-weight: 600;
}

.document-list :deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(212, 165, 116, 0.08);
}

/* 删除按钮保持危险色 */
.document-list :deep(.el-button--danger) {
  background: #F56C6C;
  border-color: #F56C6C;
}

.dialog-footer {
  text-align: right;
  padding-top: 20px;
}

/* 上传对话框样式 */
:deep(.el-dialog) {
  border-radius: 16px;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF9E8 100%);
}

:deep(.el-dialog__title) {
  color: #3D2914;
  font-weight: 600;
}

:deep(.el-upload-dragger) {
  background: #FFFEF7;
  border: 2px dashed rgba(139, 90, 43, 0.2);
  border-radius: 12px;
}

:deep(.el-upload-dragger:hover) {
  border-color: #D4A574;
}

:deep(.el-icon--upload) {
  color: #D4A574;
}
</style>