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
            <el-tag :type="row.processed ? 'success' : 'warning'">
              {{ row.processed ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180"></el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="processDocument(row.id)">处理</el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row.id)">删除</el-button>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const documents = ref([])
const showUploadDialog = ref(false)
const fileList = ref([])
const loading = ref(false)
const uploading = ref(false)

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
  try {
    await api.post(`/api/knowledge/process?doc_id=${docId}`)
    ElMessage.success('文档处理完成')
    await loadDocuments()
  } catch (error) {
    ElMessage.error('处理失败: ' + error.message)
  }
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
  try {
    await api.deleteDocument(docId)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch (error) {
    ElMessage.error('删除失败: ' + error.message)
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

.document-list {
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
  padding-top: 20px;
}
</style>