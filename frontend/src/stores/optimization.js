/**
 * 优化任务 Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { optimizationApi } from '@/api'

export const useOptimizationStore = defineStore('optimization', () => {
  const list = ref([])
  const total = ref(0)
  const loading = ref(false)
  const current = ref(null)
  const executing = ref(false)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const res = await optimizationApi.list(params)
      list.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id) {
    const res = await optimizationApi.get(id)
    current.value = res
    return res
  }

  async function create(data) {
    const res = await optimizationApi.create(data)
    await fetchList()
    return res
  }

  async function execute(id) {
    executing.value = true
    try {
      const res = await optimizationApi.execute(id)
      await fetchList()
      return res
    } finally {
      executing.value = false
    }
  }

  return {
    list,
    total,
    loading,
    current,
    executing,
    fetchList,
    fetchDetail,
    create,
    execute,
  }
})
