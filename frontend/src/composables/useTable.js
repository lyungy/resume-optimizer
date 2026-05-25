/**
 * 通用表格 composable
 * 封装分页、加载、CRUD 逻辑
 */
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRequest } from './useRequest'

export function useTable(fetchApi, options = {}) {
  const {
    pageSize: defaultPageSize = 20,
    deleteApi = null,
    deleteConfirmMsg = '确定要删除吗？',
  } = options

  const tableData = ref([])
  const currentPage = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)
  const searchParams = reactive({})

  const { loading, run: doFetch } = useRequest(fetchApi, {
    showErrorMsg: true,
  })

  const loadData = async (extraParams = {}) => {
    try {
      const params = {
        page: currentPage.value,
        page_size: pageSize.value,
        ...searchParams,
        ...extraParams,
      }
      // 清除空值
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === undefined || params[key] === null) {
          delete params[key]
        }
      })
      const res = await doFetch(params)
      tableData.value = res.items || []
      total.value = res.total || 0
    } catch (e) {
      // already handled by useRequest
    }
  }

  const handlePageChange = (page) => {
    currentPage.value = page
    loadData()
  }

  const handleSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
    loadData()
  }

  const handleSearch = (params = {}) => {
    Object.assign(searchParams, params)
    currentPage.value = 1
    loadData()
  }

  const handleDelete = async (row, idField = 'id') => {
    if (!deleteApi) {
      console.warn('useTable: deleteApi not provided')
      return
    }
    try {
      await ElMessageBox.confirm(deleteConfirmMsg, '提示', { type: 'warning' })
      await deleteApi(row[idField])
      ElMessage.success('删除成功')
      loadData()
    } catch (e) {
      if (e !== 'cancel') {
        ElMessage.error(e.message || '删除失败')
      }
    }
  }

  const resetSearch = () => {
    Object.keys(searchParams).forEach(key => {
      searchParams[key] = ''
    })
    currentPage.value = 1
    loadData()
  }

  return {
    tableData,
    currentPage,
    pageSize,
    total,
    loading,
    searchParams,
    loadData,
    handlePageChange,
    handleSizeChange,
    handleSearch,
    handleDelete,
    resetSearch,
  }
}
