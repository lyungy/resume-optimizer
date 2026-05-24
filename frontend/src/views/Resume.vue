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
        <el-table-column prop="profile" label="深度解析" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.profile ? 'success' : 'info'" size="small">
              {{ row.profile ? '已完成' : '未完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
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
            <el-button
              size="small"
              type="warning"
              @click="handleDeepAnalyze(row)"
              :loading="deepAnalyzingId === row.id"
            >
              深度解析
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

    <!-- 深度解析抽屉 -->
    <el-drawer
      v-model="deepDrawerVisible"
      title="🧠 简历深度解析"
      size="600px"
      :close-on-click-modal="false"
    >
      <div v-loading="deepAnalyzing" element-loading-text="AI 深度解析中...">
        <!-- 个人概览 -->
        <el-divider content-position="left">个人概览</el-divider>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工作年限">
            {{ deepResult.profile?.experience_profile?.total_years || '-' }}年
          </el-descriptions-item>
          <el-descriptions-item label="最高职位">
            {{ deepResult.profile?.experience_profile?.highest_title || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="管理规模">
            {{ deepResult.profile?.experience_profile?.management_scale || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="学历">
            {{ deepResult.profile?.education?.degree || '-' }}
            {{ deepResult.profile?.education?.school ? `/ ${deepResult.profile.education.school}` : '' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 核心技能（可编辑） -->
        <el-divider content-position="left">核心技能</el-divider>
        <div class="editable-tags">
          <el-tag
            v-for="(skill, idx) in allSkills"
            :key="idx"
            closable
            @close="removeSkill(idx)"
            style="margin: 2px"
          >
            {{ skill }}
          </el-tag>
          <el-input
            v-if="addingSkill"
            ref="skillInputRef"
            v-model="newSkill"
            size="small"
            style="width: 120px; margin: 2px"
            @keyup.enter="addSkill"
            @blur="addSkill"
          />
          <el-button v-else size="small" @click="startAddSkill">+ 添加技能</el-button>
        </div>

        <!-- 行业经验（可编辑） -->
        <el-divider content-position="left">行业经验</el-divider>
        <div class="editable-tags">
          <el-tag
            v-for="(industry, idx) in allIndustries"
            :key="idx"
            closable
            @close="removeIndustry(idx)"
            type="warning"
            style="margin: 2px"
          >
            {{ industry }}
          </el-tag>
          <el-input
            v-if="addingIndustry"
            ref="industryInputRef"
            v-model="newIndustry"
            size="small"
            style="width: 120px; margin: 2px"
            @keyup.enter="addIndustry"
            @blur="addIndustry"
          />
          <el-button v-else size="small" @click="startAddIndustry">+ 添加行业</el-button>
        </div>

        <!-- AI 推荐岗位（可勾选/删除/新增） -->
        <el-divider content-position="left">AI 推荐岗位</el-divider>
        <div v-for="(pos, idx) in deepResult.recommended_positions" :key="idx" class="position-item">
          <el-checkbox v-model="pos.selected" />
          <span class="position-title">{{ pos.title }}</span>
          <el-progress
            :percentage="pos.match_score"
            :stroke-width="10"
            style="width: 150px; display: inline-block; margin: 0 12px"
          />
          <el-button text type="danger" size="small" @click="removePosition(idx)">删除</el-button>
          <div class="position-reasons">
            <el-tag v-for="r in pos.match_reasons" :key="r" size="small" type="info" style="margin: 2px">
              {{ r }}
            </el-tag>
          </div>
        </div>
        <div style="margin-top: 8px">
          <el-input
            v-if="addingPosition"
            ref="positionInputRef"
            v-model="newPosition"
            size="small"
            style="width: 200px"
            placeholder="输入岗位名称"
            @keyup.enter="addPosition"
            @blur="addPosition"
          />
          <el-button v-else size="small" @click="startAddPosition">+ 添加自定义岗位</el-button>
        </div>

        <!-- 求职偏好 -->
        <el-divider content-position="left">求职偏好</el-divider>
        <el-form label-width="80px" size="small">
          <el-form-item label="期望城市">
            <el-select v-model="jobPreference.city" style="width: 200px">
              <el-option label="上海" value="上海" />
              <el-option label="北京" value="北京" />
              <el-option label="杭州" value="杭州" />
              <el-option label="深圳" value="深圳" />
              <el-option label="广州" value="广州" />
              <el-option label="成都" value="成都" />
              <el-option label="南京" value="南京" />
              <el-option label="武汉" value="武汉" />
            </el-select>
          </el-form-item>
          <el-form-item label="期望薪资">
            <el-input-number v-model="jobPreference.salary_min" :step="5000" :min="0" style="width: 120px" />
            <span style="margin: 0 8px">~</span>
            <el-input-number v-model="jobPreference.salary_max" :step="5000" :min="0" style="width: 120px" />
            <span style="margin-left: 4px">元/月</span>
          </el-form-item>
        </el-form>

        <!-- 操作按钮 -->
        <div style="margin-top: 20px; text-align: right">
          <el-button @click="deepDrawerVisible = false">关闭</el-button>
          <el-button type="primary" @click="saveProfile">保存</el-button>
          <el-button type="success" @click="startSearchMatch">
            🔍 搜索匹配
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 搜索匹配结果抽屉 -->
    <el-drawer
      v-model="matchDrawerVisible"
      title="🔍 搜索匹配结果"
      size="700px"
      :close-on-click-modal="false"
    >
      <div v-loading="searchMatching" element-loading-text="搜索匹配中...">
        <div v-if="matchResult.jobs?.length">
          <p style="margin-bottom: 16px; color: #666">
            共找到 {{ matchResult.total }} 个匹配岗位，按综合匹配度排序
          </p>

          <div v-for="(job, idx) in matchResult.jobs" :key="idx" class="match-job-card">
            <div class="match-job-header">
              <div class="match-job-title">
                <span class="rank">#{{ idx + 1 }}</span>
                {{ job.title }}
              </div>
              <div class="match-job-info">
                {{ job.salary }} · {{ job.location }} · {{ job.company_name }}
              </div>
            </div>

            <div class="match-score-bar">
              <span class="score-label">综合</span>
              <el-progress
                :percentage="job.total_score"
                :stroke-width="14"
                :color="job.total_score >= 80 ? '#67c23a' : job.total_score >= 60 ? '#e6a23c' : '#f56c6c'"
              />
              <el-tag
                :type="job.total_score >= 80 ? 'success' : job.total_score >= 60 ? 'warning' : 'danger'"
                size="small"
                style="margin-left: 8px"
              >
                {{ job.recommendation }}
              </el-tag>
            </div>

            <div class="dimension-scores">
              <div class="dim-item" v-for="(dim, key) in job.dimension_scores" :key="key">
                <span class="dim-label">{{ dimLabels[key] }}</span>
                <el-progress
                  :percentage="dim.score"
                  :stroke-width="8"
                  :show-text="false"
                  style="width: 80px"
                />
                <span class="dim-value">{{ dim.score }}</span>
              </div>
            </div>

            <div v-if="job.reasons?.length" class="match-reasons">
              <el-tag v-for="r in job.reasons" :key="r" size="small" type="success" style="margin: 2px">
                ✅ {{ r }}
              </el-tag>
            </div>
            <div v-if="job.gaps?.length" class="match-gaps">
              <el-tag v-for="g in job.gaps" :key="g" size="small" type="warning" style="margin: 2px">
                ⚠️ {{ g }}
              </el-tag>
            </div>

            <div class="match-job-actions">
              <el-button size="small" type="primary" @click="importJob(job)">导入系统</el-button>
              <el-button size="small" @click="openJobUrl(job.url)" v-if="job.url">查看JD</el-button>
            </div>
          </div>
        </div>
        <el-empty v-else-if="!searchMatching" description="暂无匹配结果，请先执行搜索" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const parsingId = ref('')
const deepAnalyzingId = ref('')

const detailVisible = ref(false)
const detailData = ref({})

// 深度解析相关
const deepDrawerVisible = ref(false)
const deepAnalyzing = ref(false)
const currentResumeId = ref('')
const deepResult = reactive({
  profile: {},
  recommended_positions: [],
  search_keywords: [],
})
const jobPreference = reactive({
  city: '上海',
  salary_min: 40000,
  salary_max: 60000,
})

// 技能编辑
const allSkills = ref([])
const addingSkill = ref(false)
const newSkill = ref('')
const skillInputRef = ref(null)

// 行业编辑
const allIndustries = ref([])
const addingIndustry = ref(false)
const newIndustry = ref('')
const industryInputRef = ref(null)

// 岗位编辑
const addingPosition = ref(false)
const newPosition = ref('')
const positionInputRef = ref(null)

// 搜索匹配相关
const matchDrawerVisible = ref(false)
const searchMatching = ref(false)
const matchResult = reactive({ total: 0, jobs: [] })

const dimLabels = {
  skill_match: '技能',
  experience_match: '经验',
  salary_match: '薪资',
  title_match: '职级',
  age_friendly: '年龄',
  industry_match: '行业',
}

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

const handleDeepAnalyze = async (row) => {
  currentResumeId.value = row.id
  deepDrawerVisible.value = true
  deepAnalyzing.value = true

  // 如果已有解析结果，直接展示
  if (row.profile) {
    Object.assign(deepResult.profile, row.profile)
    deepResult.recommended_positions = (row.recommended_positions || []).map(p => ({ ...p, selected: true }))
    allSkills.value = extractAllSkills(row.profile)
    allIndustries.value = [...(row.profile.experience_profile?.industries || [])]
    if (row.job_preference) {
      Object.assign(jobPreference, row.job_preference)
    }
    deepAnalyzing.value = false
    return
  }

  // 调用深度解析 API
  try {
    const result = await resumeApi.deepAnalyze(row.id)
    Object.assign(deepResult.profile, result.profile)
    deepResult.recommended_positions = (result.recommended_positions || []).map(p => ({ ...p, selected: true }))
    deepResult.search_keywords = result.search_keywords || []
    allSkills.value = extractAllSkills(result.profile)
    allIndustries.value = [...(result.profile.experience_profile?.industries || [])]
    ElMessage.success('深度解析完成')
    loadData()
  } catch (error) {
    ElMessage.error(error.message || '深度解析失败')
  } finally {
    deepAnalyzing.value = false
  }
}

const extractAllSkills = (profile) => {
  const skills = []
  const hard = profile?.hard_skills || {}
  for (const category of Object.values(hard)) {
    if (Array.isArray(category)) {
      skills.push(...category)
    }
  }
  return skills
}

// 技能编辑
const startAddSkill = () => {
  addingSkill.value = true
  nextTick(() => skillInputRef.value?.focus())
}
const addSkill = () => {
  if (newSkill.value.trim()) {
    allSkills.value.push(newSkill.value.trim())
    newSkill.value = ''
  }
  addingSkill.value = false
}
const removeSkill = (idx) => {
  allSkills.value.splice(idx, 1)
}

// 行业编辑
const startAddIndustry = () => {
  addingIndustry.value = true
  nextTick(() => industryInputRef.value?.focus())
}
const addIndustry = () => {
  if (newIndustry.value.trim()) {
    allIndustries.value.push(newIndustry.value.trim())
    newIndustry.value = ''
  }
  addingIndustry.value = false
}
const removeIndustry = (idx) => {
  allIndustries.value.splice(idx, 1)
}

// 岗位编辑
const startAddPosition = () => {
  addingPosition.value = true
  nextTick(() => positionInputRef.value?.focus())
}
const addPosition = () => {
  if (newPosition.value.trim()) {
    deepResult.recommended_positions.push({
      title: newPosition.value.trim(),
      match_score: 50,
      match_reasons: ['自定义添加'],
      selected: true,
    })
    newPosition.value = ''
  }
  addingPosition.value = false
}
const removePosition = (idx) => {
  deepResult.recommended_positions.splice(idx, 1)
}

// 保存画像
const saveProfile = async () => {
  try {
    // 重建 profile 中的技能和行业
    const profile = { ...deepResult.profile }
    // 更新技能到 hard_skills
    if (profile.hard_skills) {
      // 简单处理：把所有技能放到第一个类别
      const categories = Object.keys(profile.hard_skills)
      if (categories.length > 0) {
        profile.hard_skills[categories[0]] = [...allSkills.value]
      }
    }
    // 更新行业
    if (profile.experience_profile) {
      profile.experience_profile.industries = [...allIndustries.value]
    }

    await resumeApi.updateProfile(currentResumeId.value, {
      profile,
      recommended_positions: deepResult.recommended_positions,
      job_preference: { ...jobPreference },
    })
    ElMessage.success('保存成功')
    loadData()
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 搜索匹配
const startSearchMatch = async () => {
  const selected = deepResult.recommended_positions.filter(p => p.selected)
  if (!selected.length) {
    ElMessage.warning('请至少选择一个推荐岗位')
    return
  }

  matchDrawerVisible.value = true
  searchMatching.value = true

  try {
    const res = await fetch('/api/v1/collector/search-match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_id: currentResumeId.value,
        selected_positions: selected.map(p => p.title),
        city: jobPreference.city,
        salary_min: jobPreference.salary_min,
        salary_max: jobPreference.salary_max,
        limit_per_keyword: 15,
      }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '搜索失败')
    }
    const data = await res.json()
    Object.assign(matchResult, data)
    ElMessage.success(`匹配完成，共 ${data.total} 个岗位`)
  } catch (error) {
    ElMessage.error(error.message || '搜索匹配失败')
  } finally {
    searchMatching.value = false
  }
}

const importJob = async (job) => {
  try {
    await fetch('/api/v1/jd', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: job.title,
        raw_text: job.description || `${job.title}\n${job.salary}\n${job.experience}\n${job.location}`,
        source_url: job.url,
      }),
    })
    ElMessage.success(`已导入: ${job.title}`)
  } catch (error) {
    ElMessage.error('导入失败')
  }
}

const openJobUrl = (url) => {
  if (url) window.open(url, '_blank')
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

/* 深度解析抽屉 */
.editable-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.position-item {
  padding: 8px 12px;
  margin-bottom: 8px;
  background-color: #fafafa;
  border-radius: 4px;
}

.position-title {
  font-weight: bold;
  margin: 0 8px;
}

.position-reasons {
  margin-top: 4px;
  padding-left: 24px;
}

/* 搜索匹配结果 */
.match-job-card {
  padding: 16px;
  margin-bottom: 12px;
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.match-job-header {
  margin-bottom: 8px;
}

.match-job-title {
  font-size: 16px;
  font-weight: bold;
}

.match-job-title .rank {
  color: #409eff;
  margin-right: 8px;
}

.match-job-info {
  color: #666;
  font-size: 13px;
  margin-top: 4px;
}

.match-score-bar {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.score-label {
  margin-right: 8px;
  font-size: 13px;
  color: #666;
}

.dimension-scores {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

.dim-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dim-label {
  font-size: 12px;
  color: #666;
  width: 30px;
}

.dim-value {
  font-size: 12px;
  color: #333;
  width: 24px;
  text-align: right;
}

.match-reasons,
.match-gaps {
  margin-top: 4px;
}

.match-job-actions {
  margin-top: 8px;
  text-align: right;
}
</style>
