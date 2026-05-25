<template>
  <div class="jd-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>JD 管理</span>
          <div>
            <el-button @click="batchDialogVisible = true">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
            <el-button type="primary" @click="showDialog()">
              <el-icon><Plus /></el-icon>
              新增 JD
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="公司">
          <el-select v-model="searchCompanyId" placeholder="选择公司" clearable>
            <el-option
              v-for="company in companies"
              :key="company.id"
              :label="company.name"
              :value="company.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchParsed" placeholder="解析状态" clearable>
            <el-option label="已解析" :value="true" />
            <el-option label="未解析" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="searchKeyword" placeholder="职位名称" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>

      <div v-if="selectedIds.length" style="margin-bottom: 12px">
        <el-button type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除（{{ selectedIds.length }}）
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="title" label="职位名称" min-width="150" />
        <el-table-column prop="company_name" label="公司" width="120" />
        <el-table-column prop="source_url" label="来源" width="100">
          <template #default="{ row }">
            <el-link
              v-if="row.source_url"
              :href="row.source_url"
              target="_blank"
              type="primary"
              :underline="false"
            >
              查看
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="difficulty_level" label="难度" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.difficulty_level" size="small">
              {{ row.difficulty_level }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="senior_friendly" label="大龄友好" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.senior_friendly === true" type="success" size="small">是</el-tag>
            <el-tag v-else-if="row.senior_friendly === false" type="danger" size="small">否</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_parsed" label="解析状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_parsed ? 'success' : 'info'" size="small">
              {{ row.is_parsed ? '已解析' : '未解析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
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
              解析
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

    <!-- 新增对话框 -->
    <el-dialog v-model="dialogVisible" title="新增 JD" width="600px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="公司" required>
          <el-select v-model="formData.company_id" placeholder="选择公司">
            <el-option
              v-for="company in companies"
              :key="company.id"
              :label="company.name"
              :value="company.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="职位名称" required>
          <el-input v-model="formData.title" placeholder="请输入职位名称" />
        </el-form-item>
        <el-form-item label="JD 内容" required>
          <el-input
            v-model="formData.raw_text"
            type="textarea"
            :rows="10"
            placeholder="请粘贴 JD 内容"
          />
        </el-form-item>
        <el-form-item label="来源链接">
          <el-input v-model="formData.source_url" placeholder="请输入来源链接" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="JD 详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="职位名称">{{ detailData.title }}</el-descriptions-item>
        <el-descriptions-item label="公司">{{ detailData.company_name }}</el-descriptions-item>
        <el-descriptions-item label="来源" :span="2">
          <el-link
            v-if="detailData.source_url"
            :href="detailData.source_url"
            target="_blank"
            type="primary"
          >
            {{ detailData.source_url }}
          </el-link>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="工作年限">{{ detailData.experience_years || '-' }}</el-descriptions-item>
        <el-descriptions-item label="难度级别">{{ detailData.difficulty_level || '-' }}</el-descriptions-item>
        <el-descriptions-item label="大龄友好">
          <el-tag :type="detailData.senior_friendly ? 'success' : 'danger'" size="small">
            {{ detailData.senior_friendly ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="detailData.is_parsed" style="margin-top: 20px">
        <h4>硬性技能要求</h4>
        <div class="skill-tags">
          <el-tag v-for="skill in detailData.hard_skills" :key="skill" style="margin: 4px">
            {{ skill }}
          </el-tag>
        </div>

        <h4 style="margin-top: 16px">软性技能要求</h4>
        <div class="skill-tags">
          <el-tag v-for="skill in detailData.soft_skills" :key="skill" type="warning" style="margin: 4px">
            {{ skill }}
          </el-tag>
        </div>

        <h4 style="margin-top: 16px">ATS 关键词</h4>
        <div class="skill-tags">
          <el-tag v-for="kw in detailData.key_keywords" :key="kw" type="info" style="margin: 4px">
            {{ kw }}
          </el-tag>
        </div>

        <h4 v-if="detailData.senior_friendly_signals?.length" style="margin-top: 16px">大龄友好信号</h4>
        <ul>
          <li v-for="signal in detailData.senior_friendly_signals" :key="signal">{{ signal }}</li>
        </ul>

        <h4 v-if="detailData.concern_signals?.length" style="margin-top: 16px; color: #f56c6c">潜在风险信号</h4>
        <ul>
          <li v-for="signal in detailData.concern_signals" :key="signal" style="color: #f56c6c">{{ signal }}</li>
        </ul>
      </div>

      <div style="margin-top: 20px">
        <h4>原始 JD 内容</h4>
        <pre class="raw-text">{{ detailData.raw_text }}</pre>
      </div>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量导入 JD" width="700px">
      <el-alert
        type="info"
        :closable="false"
        style="margin-bottom: 16px"
      >
        <template #title>
          <span>支持 JSON 格式，每条需包含 company_name、title、raw_text 字段，可选 industry、source_url</span>
        </template>
      </el-alert>

      <el-input
        v-model="batchJsonText"
        type="textarea"
        :rows="12"
        placeholder='[
  {
    "company_name": "示例公司",
    "title": "高级工程师",
    "raw_text": "职位描述内容...",
    "industry": "互联网"
  }
]'
      />

      <div v-if="batchResult" style="margin-top: 12px">
        <el-alert
          :type="batchResult.failed > 0 ? 'warning' : 'success'"
          :closable="false"
        >
          <template #title>
            导入完成：成功 {{ batchResult.success }} 条，失败 {{ batchResult.failed }} 条
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleBatchImport"
          :loading="batchImporting"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { jdApi, companyApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const companies = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchCompanyId = ref('')
const searchParsed = ref(undefined)
const searchKeyword = ref('')
const parsingId = ref('')
const selectedIds = ref([])

const dialogVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const formData = ref({
  company_id: '',
  title: '',
  raw_text: '',
  source_url: '',
})
const detailData = ref({})

// 批量导入
const batchDialogVisible = ref(false)
const batchJsonText = ref('')
const batchImporting = ref(false)
const batchResult = ref(null)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadCompanies = async () => {
  try {
    const res = await companyApi.list({ page_size: 100 })
    companies.value = res.items
  } catch (error) {
    console.error('加载公司列表失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await jdApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      company_id: searchCompanyId.value || undefined,
      is_parsed: searchParsed.value,
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

const showDialog = () => {
  formData.value = {
    company_id: '',
    title: '',
    raw_text: '',
    source_url: '',
  }
  dialogVisible.value = true
}

const showDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const handleSubmit = async () => {
  if (!formData.value.company_id || !formData.value.title || !formData.value.raw_text) {
    ElMessage.warning('请填写必填项')
    return
  }

  submitting.value = true
  try {
    await jdApi.create(formData.value)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

const handleParse = async (row) => {
  parsingId.value = row.id
  try {
    await jdApi.parse(row.id)
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
    await ElMessageBox.confirm('确定要删除该 JD 吗？', '提示', {
      type: 'warning',
    })
    await jdApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 条 JD 吗？`,
      '批量删除',
      { type: 'warning' }
    )
    const res = await jdApi.batchDelete(selectedIds.value)
    ElMessage.success(`删除成功 ${res.deleted} 条`)
    selectedIds.value = []
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

const handleBatchImport = async () => {
  if (!batchJsonText.value.trim()) {
    ElMessage.warning('请输入 JSON 数据')
    return
  }

  let items
  try {
    items = JSON.parse(batchJsonText.value)
    if (!Array.isArray(items)) {
      ElMessage.warning('JSON 必须是数组格式')
      return
    }
  } catch (e) {
    ElMessage.error('JSON 格式错误：' + e.message)
    return
  }

  batchImporting.value = true
  batchResult.value = null
  try {
    const res = await api.post('/jd/batch-import', { items })
    batchResult.value = res
    ElMessage.success(`导入完成：成功 ${res.success} 条`)
    loadData()
    loadCompanies()
  } catch (error) {
    ElMessage.error('批量导入失败：' + error.message)
  } finally {
    batchImporting.value = false
  }
}

onMounted(() => {
  loadCompanies()
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

.raw-text {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}
</style>
