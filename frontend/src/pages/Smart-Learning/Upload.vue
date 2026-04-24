<template>
  <div class="upload-container">
    <div class="header">
      <h2>文档上传</h2>
      <p class="description">
        上传教学资料、课件、习题等文档到知识库，系统将自动进行知识结构化处理
      </p>
    </div>

    <div
      class="drop-zone"
      :class="{ 'drop-zone--active': isDragging }"
      @dragenter.prevent="isDragging = true"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <div class="drop-zone__content">
        <el-icon class="drop-zone__icon"><UploadFilled /></el-icon>
        <div class="drop-zone__text">
          <p>将文件拖拽到此处</p>
          <p class="drop-zone__hint">或 <em @click="triggerFileInput">点击选择文件</em>，支持批量上传</p>
        </div>
        <div class="drop-zone__tags">
          <el-tag size="small" type="info">PDF</el-tag>
          <el-tag size="small" type="info">DOCX</el-tag>
          <el-tag size="small" type="info">XLSX</el-tag>
          <el-tag size="small" type="info">TXT</el-tag>
          <el-tag size="small" type="info">MD</el-tag>
        </div>
        <span class="drop-zone__limit">单个文件最大 50MB，最多 20 个文件</span>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        :accept="acceptTypes"
        class="drop-zone__input"
        @change="handleFileSelect"
      />
    </div>

    <!-- 待上传文件列表 -->
    <div class="pending-list" v-if="pendingFiles.length > 0">
      <div class="pending-list__header">
        <h3>待上传文件 ({{ pendingFiles.length }})</h3>
        <el-button text type="danger" @click="clearPending">清空列表</el-button>
      </div>
      <div class="pending-list__items">
        <div class="pending-item" v-for="(item, idx) in pendingFiles" :key="idx">
          <div class="pending-item__info">
            <el-icon class="pending-item__icon" :size="20"><Document /></el-icon>
            <div class="pending-item__detail">
              <span class="pending-item__name">{{ item.file.name }}</span>
              <span class="pending-item__size">{{ formatSize(item.file.size) }}</span>
            </div>
          </div>
          <div class="pending-item__actions">
            <el-progress
              v-if="item.status === 'uploading'"
              :percentage="item.progress"
              :stroke-width="4"
              style="width: 120px; margin-right: 12px"
            />
            <el-tag v-if="item.status === 'success'" type="success" size="small">成功</el-tag>
            <el-tooltip v-else-if="item.status === 'error'" :content="item.errorMsg || '上传失败'" placement="top">
              <el-tag type="danger" size="small">失败</el-tag>
            </el-tooltip>
            <el-button
              v-if="item.status === 'pending'"
              text
              type="danger"
              @click="removePending(idx)"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div class="pending-list__footer">
        <el-button type="primary" @click="submitUpload" :loading="uploading" :disabled="!hasPendingFiles">
          {{ uploading ? `上传中 (${uploadedCount}/${totalCount})` : `开始上传 (${pendingCount} 个文件)` }}
        </el-button>
        <el-button @click="retryFailed" v-if="hasFailedFiles" type="warning">重试失败项</el-button>
        <el-button @click="refreshHistory" :loading="loading">刷新历史</el-button>
      </div>
    </div>

    <div class="upload-history" v-else>
      <div class="upload-actions">
        <el-button @click="refreshHistory" :loading="loading">刷新历史</el-button>
      </div>

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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Document, Close } from '@element-plus/icons-vue'
import api from '@/utils/api'

const acceptTypes = '.pdf,.docx,.txt,.xlsx,.md'
const maxFileSize = 50 * 1024 * 1024 // 50MB
const maxFiles = 20

const fileInputRef = ref(null)
const isDragging = ref(false)
const pendingFiles = ref([])
const uploadHistory = ref([])
const loading = ref(false)
const uploading = ref(false)

const pendingCount = computed(() => pendingFiles.value.filter(f => f.status === 'pending').length)
const hasPendingFiles = computed(() => pendingCount.value > 0)
const uploadedCount = computed(() => pendingFiles.value.filter(f => f.status === 'success' || f.status === 'error').length)
const totalCount = computed(() => pendingFiles.value.length)
const hasFailedFiles = computed(() => pendingFiles.value.some(f => f.status === 'error'))

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

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

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const validateFile = (file) => {
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  const allowed = ['.pdf', '.docx', '.txt', '.xlsx', '.md']
  if (!allowed.includes(ext)) {
    ElMessage.warning(`不支持的文件格式: ${file.name}`)
    return false
  }
  if (file.size > maxFileSize) {
    ElMessage.warning(`文件过大: ${file.name} (最大50MB)`)
    return false
  }
  return true
}

const addFiles = (files) => {
  const fileArray = Array.from(files)
  const currentCount = pendingFiles.value.length
  const remaining = maxFiles - currentCount

  if (remaining <= 0) {
    ElMessage.warning(`最多上传 ${maxFiles} 个文件`)
    return
  }

  let added = 0
  for (const file of fileArray) {
    if (added >= remaining) {
      ElMessage.warning(`已达上限，仅添加了前 ${added} 个文件`)
      break
    }
    if (validateFile(file)) {
      // 去重
      const exists = pendingFiles.value.some(f => f.file.name === file.name && f.file.size === file.size)
      if (!exists) {
        pendingFiles.value.push({ file, status: 'pending', progress: 0 })
        added++
      }
    }
  }
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    addFiles(files)
  }
}

const handleFileSelect = (e) => {
  const files = e.target?.files
  if (files?.length) {
    addFiles(files)
  }
  // 清空 input 以允许重复选择同一文件
  e.target.value = ''
}

const removePending = (idx) => {
  pendingFiles.value.splice(idx, 1)
}

const clearPending = () => {
  if (uploading.value) return
  pendingFiles.value = []
}

const submitUpload = async () => {
  const toUpload = pendingFiles.value.filter(f => f.status === 'pending' || f.status === 'error')
  if (toUpload.length === 0) {
    ElMessage.warning('没有待上传的文件')
    return
  }

  uploading.value = true

  // 重置失败文件状态
  toUpload.forEach(item => {
    if (item.status === 'error') {
      item.status = 'pending'
      item.progress = 0
      item.errorMsg = null
    }
  })

  // 并发上传，最多2个同时（大文件友好）
  const concurrency = 2
  const maxRetries = 3
  let index = 0

  const uploadNext = async () => {
    while (index < toUpload.length) {
      const item = toUpload[index++]
      item.status = 'uploading'
      item.progress = 0

      let retryCount = 0
      let success = false

      while (retryCount < maxRetries && !success) {
        try {
          await new Promise((resolve, reject) => {
            const formData = new FormData()
            formData.append('file', item.file)

            const xhr = new XMLHttpRequest()
            xhr.open('POST', '/api/documents')
            // 根据文件大小动态计算超时：基础60s + 每MB额外3s
            const timeoutMs = 60000 + Math.ceil(item.file.size / (1024 * 1024)) * 3000
            xhr.timeout = timeoutMs

            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                // 只更新不回退，避免进度条跳回
                const newProgress = Math.round((e.loaded / e.total) * 100)
                if (newProgress > item.progress) {
                  item.progress = newProgress
                }
              }
            }

            xhr.onload = () => {
              if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText))
              } else {
                try {
                  const err = JSON.parse(xhr.responseText)
                  reject(new Error(err.detail || '上传失败'))
                } catch {
                  reject(new Error(`上传失败 (${xhr.status})`))
                }
              }
            }

            xhr.onerror = () => reject(new Error('网络错误'))
            xhr.ontimeout = () => reject(new Error('上传超时'))
            xhr.send(formData)
          })

          item.progress = 100
          item.status = 'success'
          success = true
        } catch (error) {
          retryCount++
          item.errorMsg = error.message
          if (retryCount < maxRetries) {
            // 重试时进度保持不动，不回跳
            await new Promise(r => setTimeout(r, 1000 * Math.pow(2, retryCount - 1)))
          } else {
            item.status = 'error'
            console.error(`${item.file.name} 上传失败 (重试${maxRetries}次):`, error.message)
          }
        }
      }
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, toUpload.length) }, () => uploadNext())
  await Promise.all(workers)

  const successCount = toUpload.filter(f => f.status === 'success').length
  const failCount = toUpload.filter(f => f.status === 'error').length

  if (successCount > 0) {
    ElMessage.success(`成功上传 ${successCount} 个文件`)
  }
  if (failCount > 0) {
    ElMessage.warning(`${failCount} 个文件上传失败，可点击"重试失败项"重新上传`)
  }

  uploading.value = false
  await loadHistory()

  // 5秒后自动清除已完成的
  setTimeout(() => {
    pendingFiles.value = pendingFiles.value.filter(f => f.status === 'pending' || f.status === 'uploading')
    if (pendingFiles.value.length === 0) {
      pendingFiles.value = []
    }
  }, 5000)
}

const retryFailed = () => {
  pendingFiles.value.forEach(item => {
    if (item.status === 'error') {
      item.status = 'pending'
      item.progress = 0
      item.errorMsg = null
    }
  })
  submitUpload()
}

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

const refreshHistory = async () => {
  await loadHistory()
  ElMessage.success('刷新成功')
}

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
  padding: 24px;
  background: linear-gradient(180deg, #FFFEF7 0%, #FFF9E8 100%);
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(139, 90, 43, 0.08);
  min-height: calc(100vh - 140px);
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-weight: 600;
  margin-bottom: 8px;
}

.description {
  color: #8B7355;
  margin-top: 8px;
  font-size: 14px;
}

/* 拖拽区域 */
.drop-zone {
  border: 2px dashed rgba(139, 90, 43, 0.2);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 254, 247, 0.6);
  position: relative;
}

.drop-zone:hover {
  border-color: #D4A574;
  background: rgba(255, 249, 232, 0.6);
}

.drop-zone--active {
  border-color: #C4956A;
  background: rgba(212, 165, 116, 0.12);
  transform: scale(1.01);
  box-shadow: 0 0 0 4px rgba(212, 165, 116, 0.1);
}

.drop-zone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.drop-zone__icon {
  font-size: 48px;
  color: #D4A574;
  transition: transform 0.3s ease;
}

.drop-zone--active .drop-zone__icon {
  transform: translateY(-4px) scale(1.1);
}

.drop-zone__text p {
  margin: 0;
  color: #3D2914;
  font-size: 16px;
  font-weight: 500;
}

.drop-zone__text em {
  color: #D4A574;
  font-style: normal;
  cursor: pointer;
  text-decoration: underline;
}

.drop-zone__hint {
  font-size: 13px !important;
  color: #8B7355 !important;
  font-weight: 400 !important;
}

.drop-zone__tags {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.drop-zone__tags :deep(.el-tag) {
  background: rgba(139, 90, 43, 0.08);
  border-color: rgba(139, 90, 43, 0.15);
  color: #8B7355;
}

.drop-zone__limit {
  font-size: 12px;
  color: #8B7355;
}

.drop-zone__input {
  display: none;
}

/* 待上传列表 */
.pending-list {
  margin-top: 24px;
}

.pending-list__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.pending-list__header h3 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.pending-list__items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
  padding: 4px 0;
}

.pending-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border: 1px solid rgba(139, 90, 43, 0.1);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.pending-item:hover {
  border-color: #D4A574;
  box-shadow: 0 2px 8px rgba(212, 165, 116, 0.1);
}

.pending-item__info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.pending-item__icon {
  color: #D4A574;
  flex-shrink: 0;
}

.pending-item__detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pending-item__name {
  font-size: 14px;
  color: #3D2914;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pending-item__size {
  font-size: 12px;
  color: #8B7355;
}

.pending-item__actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pending-list__footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 上传历史 */
.upload-history {
  margin-top: 24px;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.upload-history h3 {
  font-family: 'Noto Serif SC', 'Source Han Serif CN', Georgia, serif;
  color: #3D2914;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.upload-history :deep(.el-table) {
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
}

.upload-history :deep(.el-table th.el-table__cell) {
  background: linear-gradient(135deg, #FFFEF7 0%, #FFF5E6 100%);
  color: #3D2914;
  font-weight: 600;
}

.upload-history :deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(212, 165, 116, 0.08);
}

.upload-history :deep(.el-button--danger) {
  background: #F56C6C;
  border-color: #F56C6C;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #D4A574 0%, #C4956A 100%);
}
</style>
