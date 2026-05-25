/**
 * 通用 API 请求 composable
 * 封装 loading / error / data 三态
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useRequest(apiFn, options = {}) {
  const {
    immediate = false,
    onSuccess = null,
    onError = null,
    showSuccessMsg = false,
    successMsg = '操作成功',
    showErrorMsg = true,
  } = options

  const loading = ref(false)
  const data = ref(null)
  const error = ref(null)

  const run = async (...args) => {
    loading.value = true
    error.value = null
    try {
      const result = await apiFn(...args)
      data.value = result
      if (showSuccessMsg) {
        ElMessage.success(successMsg)
      }
      if (onSuccess) {
        onSuccess(result)
      }
      return result
    } catch (e) {
      error.value = e
      if (showErrorMsg) {
        ElMessage.error(e.message || '请求失败')
      }
      if (onError) {
        onError(e)
      }
      throw e
    } finally {
      loading.value = false
    }
  }

  if (immediate) {
    run()
  }

  return {
    loading,
    data,
    error,
    run,
  }
}
