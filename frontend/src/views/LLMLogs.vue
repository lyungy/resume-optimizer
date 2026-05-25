<template>
  <div class="llm-logs-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_calls || 0 }}</div>
            <div class="stat-label">总调用次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value" style="color: #67c23a">{{ stats.success_rate || 0 }}%</div>
            <div class="stat-label">成功率</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ formatTokens(stats.total_tokens) }}</div>
            <div class="stat-label">总 Token</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ stats.avg_duration_ms || 0 }}ms</div>
            <div class="stat-label">平均耗时</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <span>LLM 调用日志</span>
      </template>

      <!-- 筛选 -->
      <el-form :inline="true" class="search-form">
        <el-form-item label="功能">
          <el-select v-model="filters.feature" placeholder="全部" clearable>
            <el-option label="智能解析" value="智能解析" />
            <el-option label="职业画像" value="职业画像" />
            <el-option label="JD解析" value="JD解析" />
            <el-option label="简历优化" value="简历优化" />
            <el-option label="面试攻略" value="面试攻略" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="feature" label="功能" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.feature }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="llm_model" label="模型" width="150" />
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_tokens" label="Token" width="100" align="right">
          <template #default="{ row }">
            {{ row.total_tokens ? row.total_tokens.toLocaleString() : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="100" align="right">
          <template #default="{ row }">
            {{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="重试" width="60" align="center">
          <template #default="{ row }">
            {{ row.retry_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="LLM 调用详情" width="800px">
      <div v-if="detailData">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="功能">{{ detailData.feature }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ detailData.llm_model }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="detailData.status === 'success' ? 'success' : 'danger'" size="small">
              {{ detailData.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时">{{ detailData.duration_ms }}ms</el-descriptions-item>
          <el-descriptions-item label="输入 Token">{{ detailData.input_tokens?.toLocaleString() || '-' }}</el-descriptions-item>
          <el-descriptions-item label="输出 Token">{{ detailData.output_tokens?.toLocaleString() || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联ID" :span="2">{{ detailData.related_id || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="detailData.error_message" label="错误信息" :span="2">
            <span style="color: #f56c6c">{{ detailData.error_message }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-tabs style="margin-top: 16px">
          <el-tab-pane label="System Prompt">
            <pre class="prompt-text">{{ detailData.system_prompt || '无' }}</pre>
          </el-tab-pane>
          <el-tab-pane label="User Prompt">
            <pre class="prompt-text">{{ detailData.user_prompt || '无' }}</pre>
          </el-tab-pane>
          <el-tab-pane label="原始返回">
            <pre class="prompt-text">{{ detailData.raw_response || '无' }}</pre>
          </el-tab-pane>
          <el-tab-pane label="解析结果">
            <pre class="prompt-text">{{ JSON.stringify(detailData.parsed_result, null, 2) || '无' }}</pre>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { llmLogApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stats = ref({})

const filters = reactive({
  feature: '',
  status: '',
})

const detailVisible = ref(false)
const detailData = ref(null)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatTokens = (tokens) => {
  if (!tokens) return '0'
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toString()
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await llmLogApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      feature: filters.feature || undefined,
      status: filters.status || undefined,
    })
    tableData.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    stats.value = await llmLogApi.stats()
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const resetFilters = () => {
  filters.feature = ''
  filters.status = ''
  currentPage.value = 1
  loadData()
}

const showDetail = async (row) => {
  try {
    detailData.value = await llmLogApi.get(row.id)
    detailVisible.value = true
  } catch (error) {
    ElMessage.error(error.message)
  }
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.search-form {
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

.prompt-text {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.6;
  font-family: monospace;
}
</style>
