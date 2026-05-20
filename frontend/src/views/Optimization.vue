<template>
  <div class="optimization-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>简历优化</span>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            新建优化任务
          </el-button>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="jd_title" label="职位" min-width="120" />
        <el-table-column prop="company_name" label="公司" width="100" />
        <el-table-column prop="resume_name" label="简历" width="120" />
        <el-table-column prop="llm_provider" label="LLM" width="80" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="match_score" label="匹配度" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.match_score" :style="{ color: getScoreColor(row.match_score) }">
              {{ row.match_score }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="success"
              @click="handleExecute(row)"
              :loading="executingId === row.id"
            >
              执行优化
            </el-button>
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'completed'"
              size="small"
              type="primary"
              @click="handleDownloadResume(row)"
            >
              下载简历
            </el-button>
            <el-button
              v-if="row.status === 'completed' && !row.has_interview_guide"
              size="small"
              type="warning"
              @click="handleGenerateGuide(row)"
            >
              生成攻略
            </el-button>
            <el-button
              v-if="row.has_interview_guide"
              size="small"
              type="info"
              @click="viewGuide(row)"
            >
              查看攻略
            </el-button>
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

    <!-- 新建优化任务对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建优化任务" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="JD" required>
          <el-select v-model="createForm.jd_id" placeholder="选择 JD" filterable>
            <el-option
              v-for="jd in jdList"
              :key="jd.id"
              :label="`${jd.title} - ${jd.company_name}`"
              :value="jd.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="简历" required>
          <el-select v-model="createForm.resume_id" placeholder="选择简历" filterable>
            <el-option
              v-for="resume in resumeList"
              :key="resume.id"
              :label="resume.name"
              :value="resume.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="LLM 模型">
          <el-select v-model="createForm.llm_provider" placeholder="选择模型（默认 MiMo）">
            <el-option label="MiMo" value="xiaomi-coding" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="优化结果详情" width="800px">
      <div v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="职位">{{ detailData.jd_title }}</el-descriptions-item>
          <el-descriptions-item label="公司">{{ detailData.company_name }}</el-descriptions-item>
          <el-descriptions-item label="匹配度">
            <el-progress
              :percentage="detailData.match_score || 0"
              :stroke-width="20"
              :text-inside="true"
            />
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailData.status)">
              {{ getStatusText(detailData.status) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="detailData.keyword_coverage" style="margin-top: 20px">
          <h4>关键词覆盖</h4>
          <p>覆盖率：{{ (detailData.keyword_coverage.coverage_rate * 100).toFixed(1) }}%</p>
          <div>
            <span>已覆盖：</span>
            <el-tag
              v-for="kw in detailData.keyword_coverage.matched"
              :key="kw"
              type="success"
              size="small"
              style="margin: 2px"
            >
              {{ kw }}
            </el-tag>
          </div>
          <div style="margin-top: 8px">
            <span>未覆盖：</span>
            <el-tag
              v-for="kw in detailData.keyword_coverage.missing"
              :key="kw"
              type="danger"
              size="small"
              style="margin: 2px"
            >
              {{ kw }}
            </el-tag>
          </div>
        </div>

        <div v-if="detailData.suggestions?.length" style="margin-top: 20px">
          <h4>优化建议</h4>
          <ul>
            <li v-for="s in detailData.suggestions" :key="s">{{ s }}</li>
          </ul>
        </div>

        <div v-if="detailData.ats_tips?.length" style="margin-top: 20px">
          <h4>ATS 优化建议</h4>
          <ul>
            <li v-for="tip in detailData.ats_tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api, { optimizationApi, jdApi, resumeApi, interviewApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const createDialogVisible = ref(false)
const creating = ref(false)
const createForm = ref({
  jd_id: '',
  resume_id: '',
  llm_provider: '',
})
const jdList = ref([])
const resumeList = ref([])

const detailDialogVisible = ref(false)
const detailData = ref(null)
const executingId = ref('')

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '待执行',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

const getScoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await optimizationApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const loadSelections = async () => {
  try {
    const [jdRes, resumeRes] = await Promise.all([
      jdApi.list({ page_size: 100, is_parsed: true }),
      resumeApi.list({ page_size: 100 }),
    ])
    jdList.value = jdRes.items
    resumeList.value = resumeRes.items
  } catch (error) {
    console.error('加载选项失败:', error)
  }
}

const showCreateDialog = () => {
  createForm.value = {
    jd_id: '',
    resume_id: '',
    llm_provider: '',
  }
  loadSelections()
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!createForm.value.jd_id || !createForm.value.resume_id) {
    ElMessage.warning('请选择 JD 和简历')
    return
  }

  creating.value = true
  try {
    await optimizationApi.create(createForm.value)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    creating.value = false
  }
}

const handleExecute = async (row) => {
  executingId.value = row.id
  try {
    await optimizationApi.execute(row.id)
    ElMessage.success('优化完成')
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    executingId.value = ''
  }
}

const showDetail = (row) => {
  detailData.value = row
  detailDialogVisible.value = true
}

const handleGenerateGuide = async (row) => {
  try {
    const guide = await interviewApi.create({ optimization_id: row.id })
    await interviewApi.generate(guide.id)
    ElMessage.success('面试攻略生成成功')
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const viewGuide = async (row) => {
  try {
    const guide = await interviewApi.getByOptimization(row.id)
    router.push(`/interview?id=${guide.id}`)
  } catch (error) {
    ElMessage.error(error.message)
  }
}

const handleDownloadResume = async (row) => {
  try {
    const response = await api.get(`/optimization/${row.id}/download`, {
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `优化简历_${row.company_name || ''}_${row.jd_title || ''}.docx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
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
</style>
