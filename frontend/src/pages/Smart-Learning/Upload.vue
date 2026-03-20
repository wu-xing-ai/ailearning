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
        v-model:file-list="fileList"
        class="upload-demo"
        action="/api/documents"
        :auto-upload="false"
        drag
        multiple
        :on-preview="handlePreview"
        :on-remove="handleRemove"
        :on-exceed="handleExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOCX、XLSX、TXT、Markdown 等格式，单个文件最大 50MB
          </div>
        </template>
      </el-upload>
    </div>

    <div class="upload-actions">
      <el-button type="primary" @click="submitUpload">开始上传</el-button>
      <el-button @click="handleBatchUpload">批量上传</el-button>
    </div>

    <div class="upload-history">
      <h3>上传历史</h3>
      <el-table :data="uploadHistory" style="width: 100%">
        <el-table-column prop="filename" label="文件名" width="200"></el-table-column>
        <el-table-column prop="size" label="大小" width="80"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180"></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const fileList = ref([])
const uploadHistory = ref([
  {
    filename: '高一数学教材.pdf',
    size: '25.6 MB',
    status: 'success',
    upload_time: '2024-01-15 14:30:22'
  },
  {
    filename: '英语语法总结.docx',
    size: '3.2 MB',
    status: 'success',
    upload_time: '2024-01-16 09:15:33'
  },
  {
    filename: '物理实验指南.xlsx',
    size: '1.8 MB',
    status: 'failed',
    upload_time: '2024-01-17 16:45:12'
  }
])

const handleRemove = (uploadFile, uploadFiles) => {
  console.log(uploadFiles)
}

const handlePreview = (uploadFile) => {
  console.log(uploadFile)
}

const handleExceed = (files, uploadFiles) => {
  ElMessage.warning(`最多只能选择 ${files.length} 个文件`)
}

const submitUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  ElMessage.info('开始上传文件...')

  // 模拟上传过程
  setTimeout(() => {
    fileList.value.forEach(file => {
      const historyItem = {
        filename: file.name,
        size: formatFileSize(file.size),
        status: 'success',
        upload_time: new Date().toLocaleString()
      }
      uploadHistory.value.unshift(historyItem)
    })
    fileList.value = []
    ElMessage.success('文件上传成功！')
  }, 1500)
}

const handleBatchUpload = () => {
  ElMessageBox.confirm(
    '确定要批量上传所有选中的文件吗？',
    '批量上传',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    ElMessage.success('批量上传开始')
  })
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}
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