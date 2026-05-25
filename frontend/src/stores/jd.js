/**
 * JD Store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { jdApi } from '@/api'

export const useJdStore = defineStore('jd', () => {
  const list = ref([])
  const total = ref(0)
  const loading = ref(false)
  const current = ref(null)

  async function fetchList(params = {}) {
    loading.value = true
    try {
      const res = await jdApi.list(params)
      list.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id) {
    const res = await jdApi.get(id)
    current.value = res
    return res
  }

  async function create(data) {
    const res = await jdApi.create(data)
    await fetchList()
    return res
  }

  async function parse(id, provider, model) {
    const res = await jdApi.parse(id, provider, model)
    await fetchList()
    return res
  }

  async function remove(id) {
    await jdApi.delete(id)
    await fetchList()
  }

  return {
    list,
    total,
    loading,
    current,
    fetchList,
    fetchDetail,
    create,
    parse,
    remove,
  }
})
