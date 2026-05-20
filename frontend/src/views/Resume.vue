<template>
  <div class="resume-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>简历管理</span>
          <el-upload
            :show-file-list="false"
            :before-upload="beforeUpload"
            :http-request="handleUpload"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              上传简历
            </el-button>
          </el-upload>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="搜索">
          <el-input v-model="searchKeyword" placeholder="简历名称" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="name" label="简历名称" min-width="200" />
        <el-table-column prop="experience_years" label="工作年限" width="100" align="center">
          <template #default="{ row }">
            {{ row.experience_years ? `${row.experience_years}年` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="skills" label="技能标签" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="skill in (row.skills || []).slice(0, 5)"
              :key="skill"
              size="small"
              style="margin: 2px"
            >
              {{ skill }}
            </el-tag>
            <el-tag v-if="(row.skills || []).length > 5" size="small" type="info">
              +{{ row.skills.length - 5 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_parsed" label="解析状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_parsed ? 'success' : 'info'" size="small">
              {{ row.is_parsed ? '已解析' : '未解析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <el-button
              v-if="!row.is_parsed"
              size="small"
              type="success"
              @click="handleParse(row)"
              :loading="parsingId === row.id"
            >
              AI 解析
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="简历详情" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="简历名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="工作年限">
          {{ detailData.experience_years ? `${detailData.experience_years}年` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="最高学历">{{ detailData.education?.degree || '-' }}</el-descriptions-item>
        <el-descriptions-item label="毕业院校">{{ detailData.education?.school || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px">
        <h4>技能标签</h4>
        <div class="skill-tags">
          <el-tag v-for="skill in detailData.skills" :key="skill" type="success" style="margin: 4px">
            {{ skill }}
          </el-tag>
          <span v-if="!detailData.skills?.length" style="color: #999">暂无（点击 AI 解析提取）</span>
        </div>
      </div>

      <div v-if="detailData.work_experience?.length" style="margin-top: 20px">
        <h4>工作经历</h4>
        <div v-for="work in detailData.work_experience" :key="work.company" class="work-item">
          <div class="work-header">
            <strong>{{ work.company }}</strong> - {{ work.title }}
            <span class="work-period">{{ work.period }}</span>
          </div>
          <ul v-if="work.highlights?.length">
            <li v-for="h in work.highlights" :key="h">{{ h }}</li>
          </ul>
        </div>
      </div>

      <div v-if="detailData.projects?.length" style="margin-top: 20px">
        <h4>项目经历</h4>
        <div v-for="proj in detailData.projects" :key="proj.name" class="work-item">
          <div class="work-header">
            <strong>{{ proj.name }}</strong>
            <span v-if="proj.role"> | {{ proj.role }}</span>
            <span class="work-period">{{ proj.period }}</span>
          </div>
          <p v-if="proj.description">{{ proj.description }}</p>
          <ul v-if="proj.highlights?.length">
            <li v-for="h in proj.highlights" :key="h">{{ h }}</li>
          </ul>
        </div>
      </div>

      <div style="margin-top: 20px">
        <h4>原始简历内容</h4>
        <pre class="resume-text">{{ detailData.parsed_content?.text || '暂无内容' }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const parsingId = ref('')

const detailVisible = ref(false)
const detailData = ref({})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await resumeApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const beforeUpload = (file) => {
  const isDocx = file.name.endsWith('.docx')
  if (!isDocx) {
    ElMessage.error('只能上传 .docx 格式的文件')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

const handleUpload = async (options) => {
  try {
    await resumeApi.upload(options.file)
    ElMessage.success('上传成功')
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const showDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const handleParse = async (row) => {
  parsingId.value = row.id
  try {
    await resumeApi.parse(row.id)
    ElMessage.success('解析完成')
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    parsingId.value = ''
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该简历吗？', '提示', {
      type: 'warning',
    })
    await resumeApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.resume-text {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}

.work-item {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #fafafa;
  border-radius: 4px;
}

.work-header {
  margin-bottom: 8px;
}

.work-period {
  color: #999;
  margin-left: 8px;
  font-size: 13px;
}
</style>
