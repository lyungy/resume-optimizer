<template>
  <div class="interview-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>面试攻略</span>
        </div>
      </template>

      <div v-if="selectedIds.length" style="margin-bottom: 12px">
        <el-button type="danger" @click="handleBatchDelete">
          <el-icon><Delete /></el-icon>
          批量删除（{{ selectedIds.length }}）
        </el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" border @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="jd_title" label="职位" min-width="120" />
        <el-table-column prop="company_name" label="公司" width="120" />
        <el-table-column label="知识点" width="80" align="center">
          <template #default="{ row }">
            {{ row.knowledge_points?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="面试题" width="80" align="center">
          <template #default="{ row }">
            {{ row.high_frequency_questions?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">查看攻略</el-button>
            <el-button
              v-if="row.export_docx_path"
              size="small"
              type="success"
              @click="handleDownload(row)"
            >
              下载文档
            </el-button>
            <el-button
              v-if="!row.knowledge_points"
              size="small"
              type="warning"
              @click="handleGenerate(row)"
              :loading="generatingId === row.id"
            >
              生成内容
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

    <!-- 攻略详情对话框 -->
    <el-dialog v-model="detailVisible" title="面试攻略" width="900px">
      <div v-if="detailData" class="guide-content">
        <!-- 知识点清单 -->
        <div v-if="detailData.knowledge_points?.length" class="section">
          <h3>📚 知识点清单</h3>
          <el-collapse>
            <el-collapse-item
              v-for="(kp, idx) in detailData.knowledge_points"
              :key="idx"
              :title="`${kp.category} (优先级: ${kp.priority}, 预计 ${kp.estimated_prep_hours} 小时)`"
            >
              <ul>
                <li v-for="point in kp.points" :key="point">{{ point }}</li>
              </ul>
              <div v-if="kp.study_resources?.length" style="margin-top: 8px">
                <strong>学习资源：</strong>
                <ul>
                  <li v-for="res in kp.study_resources" :key="res">{{ res }}</li>
                </ul>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 高频面试题 -->
        <div v-if="detailData.high_frequency_questions?.length" class="section">
          <h3>❓ 高频面试题</h3>
          <el-collapse>
            <el-collapse-item
              v-for="(q, idx) in detailData.high_frequency_questions"
              :key="idx"
              :title="`Q${idx + 1}: ${q.question}`"
            >
              <p><strong>分类：</strong>{{ q.category }} | <strong>难度：</strong>{{ q.difficulty }}</p>
              <div v-if="q.answer_template">
                <strong>答题模板：</strong>
                <p class="answer-template">{{ q.answer_template }}</p>
              </div>
              <div v-if="q.key_points?.length">
                <strong>回答要点：</strong>
                <ul>
                  <li v-for="point in q.key_points" :key="point">{{ point }}</li>
                </ul>
              </div>
              <div v-if="q.common_mistakes?.length">
                <strong style="color: #f56c6c">常见错误：</strong>
                <ul>
                  <li v-for="mistake in q.common_mistakes" :key="mistake" style="color: #f56c6c">
                    {{ mistake }}
                  </li>
                </ul>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- 准备策略 -->
        <div v-if="detailData.preparation_strategy" class="section">
          <h3>📅 准备策略</h3>
          <p>建议准备天数：{{ detailData.preparation_strategy.total_days }} 天</p>

          <el-timeline v-if="detailData.preparation_strategy.daily_plan?.length">
            <el-timeline-item
              v-for="day in detailData.preparation_strategy.daily_plan"
              :key="day.day"
              :timestamp="`第 ${day.day} 天 (${day.hours} 小时)`"
              placement="top"
            >
              <el-card>
                <h4>{{ day.focus }}</h4>
                <ul>
                  <li v-for="task in day.tasks" :key="task">{{ task }}</li>
                </ul>
              </el-card>
            </el-timeline-item>
          </el-timeline>

          <div v-if="detailData.preparation_strategy.tips?.length">
            <strong>面试技巧：</strong>
            <ul>
              <li v-for="tip in detailData.preparation_strategy.tips" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </div>

        <!-- 公司调研 -->
        <div v-if="detailData.company_research" class="section">
          <h3>🏢 公司调研</h3>
          <div v-if="detailData.company_research.what_to_prepare?.length">
            <strong>需要了解的信息：</strong>
            <ul>
              <li v-for="item in detailData.company_research.what_to_prepare" :key="item">
                {{ item }}
              </li>
            </ul>
          </div>
          <div v-if="detailData.company_research.questions_to_ask?.length">
            <strong>可以反问的问题：</strong>
            <ul>
              <li v-for="q in detailData.company_research.questions_to_ask" :key="q">{{ q }}</li>
            </ul>
          </div>
          <div v-if="detailData.company_research.red_flags?.length">
            <strong style="color: #f56c6c">需要注意的信号：</strong>
            <ul>
              <li v-for="flag in detailData.company_research.red_flags" :key="flag" style="color: #f56c6c">
                {{ flag }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api, { interviewApi, downloadFile } from '@/api'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const detailData = ref(null)
const generatingId = ref('')
const selectedIds = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await interviewApi.list({
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

const showDetail = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const handleGenerate = async (row) => {
  generatingId.value = row.id
  try {
    await interviewApi.generate(row.id)
    ElMessage.success('生成成功')
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    generatingId.value = ''
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该攻略吗？', '提示', { type: 'warning' })
    await interviewApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  }
}

const handleDownload = async (row) => {
  try {
    const filename = `面试攻略_${row.company_name || ''}_${row.jd_title || ''}.docx`
    await downloadFile(`/interview/${row.id}/download`, filename)
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  }
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map(r => r.id)
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 条攻略吗？`,
      '批量删除',
      { type: 'warning' }
    )
    const res = await interviewApi.batchDelete(selectedIds.value)
    ElMessage.success(`删除成功 ${res.deleted} 条`)
    selectedIds.value = []
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

.guide-content {
  max-height: 600px;
  overflow-y: auto;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  margin-bottom: 12px;
  color: #333;
}

.answer-template {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
}
</style>
