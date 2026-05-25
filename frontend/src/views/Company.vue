<template>
  <div class="company-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公司管理</span>
          <el-button type="primary" @click="showDialog()">
            <el-icon><Plus /></el-icon>
            新增公司
          </el-button>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="搜索">
          <el-input v-model="searchKeyword" placeholder="公司名称/行业" clearable />
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
        <el-table-column prop="name" label="公司名称" min-width="120" />
        <el-table-column prop="industry" label="行业" width="120" />
        <el-table-column prop="size" label="规模" width="100" />
        <el-table-column prop="jd_count" label="JD数量" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDialog(row)">编辑</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑公司' : '新增公司'"
      width="500px"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="公司名称" required>
          <el-input v-model="formData.name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="行业">
          <el-input v-model="formData.industry" placeholder="请输入行业" />
        </el-form-item>
        <el-form-item label="规模">
          <el-select v-model="formData.size" placeholder="请选择">
            <el-option label="1-50人" value="1-50人" />
            <el-option label="50-150人" value="50-150人" />
            <el-option label="150-500人" value="150-500人" />
            <el-option label="500-2000人" value="500-2000人" />
            <el-option label="2000人以上" value="2000人以上" />
          </el-select>
        </el-form-item>
        <el-form-item label="官网">
          <el-input v-model="formData.website" placeholder="请输入官网地址" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="formData.notes" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { companyApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const selectedIds = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formData = ref({
  id: '',
  name: '',
  industry: '',
  size: '',
  website: '',
  notes: '',
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await companyApi.list({
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

const showDialog = (row) => {
  if (row) {
    isEdit.value = true
    formData.value = {
      id: row.id,
      name: row.name,
      industry: row.industry || '',
      size: row.size || '',
      website: row.website || '',
      notes: row.notes || '',
    }
  } else {
    isEdit.value = false
    formData.value = {
      id: '',
      name: '',
      industry: '',
      size: '',
      website: '',
      notes: '',
    }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formData.value.name) {
    ElMessage.warning('请输入公司名称')
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await companyApi.update(formData.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await companyApi.create(formData.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该公司吗？', '提示', {
      type: 'warning',
    })
    await companyApi.delete(row.id)
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
      `确定要删除选中的 ${selectedIds.value.length} 家公司吗？`,
      '批量删除',
      { type: 'warning' }
    )
    const res = await companyApi.batchDelete(selectedIds.value)
    let msg = `删除成功 ${res.deleted} 家`
    if (res.skipped > 0) {
      msg += `，跳过 ${res.skipped} 家（存在关联 JD）`
    }
    ElMessage.success(msg)
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

.search-form {
  margin-bottom: 20px;
}
</style>
