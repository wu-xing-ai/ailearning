<template>
  <div class="library-container">
    <div class="header">
      <h2>知识库管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showUploadDialog = true">上传文档</el-button>
        <el-button @click="refreshLibrary">刷新</el-button>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="document-list">
      <el-table :data="documents" style="width: 100%">
        <el-table-column prop="filename" label="文件名" width="200"></el-table-column>
        <el-table-column prop="file_type" label="类型" width="100"></el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.processed ? 'success' : 'warning'">
              {{ row.processed ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180"></el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="processDocument(row.id)">处理</el-button>
            <el-button size="small" type="danger" @click="deleteDocument(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传文档" width="30%">
      <el-upload
        drag
        action="/api/documents"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        :limit="10"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、DOCX、XLSX、TXT 等格式
          </div>
        </template>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="uploadDocuments">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const documents = ref([])
const showUploadDialog = ref(false)
const fileList = ref([])

// 模拟文档数据
const mockDocuments = [
  {
    id: '1',
    filename: '数学教材.pdf',
    file_type: 'PDF',
    processed: true,
    created_at: '2024-01-15 14:30'
  },
  {
    id: '2',
    filename: '英语课文.docx',
    file_type: 'DOCX',
    processed: false,
    created_at: '2024-01-16 09:15'
  },
  {
    id: '3',
    filename: '物理习题集.xlsx',
    file_type: 'XLSX',
    processed: false,
    created_at: '2024-01-17 16:45'
  }
]

onMounted(() => {
  documents.value = mockDocuments
})

const refreshLibrary = async () => {
  // 这里应该调用API获取真实数据
  ElMessage.info('刷新知识库')
}

const processDocument = (docId) => {
  // 调用API处理文档
  ElMessage.success(`开始处理文档 ${docId}`)
}

const deleteDocument = (docId) => {
  // 调用API删除文档
  ElMessage.success(`删除文档 ${docId}`)
  documents.value = documents.value.filter(doc => doc.id !== docId)
}

const handleFileChange = (file) => {
  fileList.value = [...fileList.value, file]
}

const uploadDocuments = () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  ElMessage.success(`成功上传 ${fileList.value.length} 个文件`)
  showUploadDialog.value = false
  fileList.value = []
}
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