<template>
  <div class="upload-container">
    <div class="header">
      <h2>文档上传</h2>
      <p class="description">
        上传教学资料、课件、习题等文档到知识库，系统将自动进行知识结构化处理
      </p>
    </div>

    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        action="#"
        :auto-upload="false"
        drag
        multiple
        :on-change="handleFileChange"
        :on-remove="handleRemove"
        :file-list="fileList"
        :limit="20"
        accept=".pdf,.docx,.txt,.xlsx,.md"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOCX、XLSX、TXT、MD 格式，单个文件最大 50MB
          </div>
        </template>
      </el-upload>
    </div>

    <div class="upload-actions">
      <el-button type="primary" @click="submitUpload" :loading="uploading">开始上传</el-button>
      <el-button @click="refreshHistory" :loading="loading">刷新历史</el-button>
    </div>

    <div class="upload-history">
      <h3>上传历史</h3>
      <el-table :data="uploadHistory" style="width: 100%" v-loading="loading">
        <el-table-column prop="filename" label="文件名" width="250"></el-table-column>
        <el-table-column prop="file_type" label="类型" width="80"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.processed ? 'success' : 'warning'">
              {{ row.processed ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180"></el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && uploadHistory.length === 0" description="暂无上传记录" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

const fileList = ref([])
const uploadHistory = ref([])
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

// 加载上传历史
const loadHistory = async () => {
  loading.value = true
  try {
    const result = await api.getDocuments()
    uploadHistory.value = result.map(doc => ({
      ...doc,
      created_at: formatDateTime(doc.created_at)
    }))
  } catch (error) {
    ElMessage.error('加载上传历史失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 刷新历史
const refreshHistory = async () => {
  await loadHistory()
  ElMessage.success('刷新成功')
}

// 文件选择变化
const handleFileChange = (file, files) => {
  fileList.value = files
}

// 文件移除
const handleRemove = (file, files) => {
  fileList.value = files
}

// 提交上传
const submitUpload = async () => {
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
      ElMessage.warning(`${failCount} 个文件上传失败`)
    }

    fileList.value = []
    await loadHistory()  // 刷新上传历史
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

// 删除文档
const handleDelete = async (docId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文档吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await api.deleteDocument(docId)
    ElMessage.success('删除成功')
    await loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.upload-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header {
  margin-bottom: 20px;
}

.description {
  color: #666;
  margin-top: 10px;
}

.upload-area {
  margin: 20px 0;
}

.upload-history {
  margin-top: 30px;
}

.upload-actions {
  margin: 20px 0;
  text-align: right;
}
</style>