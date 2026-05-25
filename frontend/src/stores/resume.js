/**
 * 简历 Store
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { resumeApi } from '@/api'

export const useResumeStore = defineStore('resume', () => {
  // 列表数据
  const list = ref([])
  const total = ref(0)
  const loading = ref(false)

  // 当前详情
  const current = ref(null)

  // 职业画像结果
  const deepResult = reactive({
    profile: {},
    recommended_positions: [],
    search_keywords: [],
  })

  // 求职偏好
  const jobPreference = reactive({
    city: '上海',
    salary_min: 40000,
    salary_max: 60000,
  })

  // 加载列表
  async function fetchList(params = {}) {
    loading.value = true
    try {
      const res = await resumeApi.list(params)
      list.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  // 获取详情
  async function fetchDetail(id) {
    const res = await resumeApi.get(id)
    current.value = res
    return res
  }

  // 智能解析
  async function parse(id, provider) {
    const res = await resumeApi.parse(id, provider)
    // 刷新列表
    await fetchList()
    return res
  }

  // 职业画像
  async function deepAnalyze(id, provider) {
    const res = await resumeApi.deepAnalyze(id, provider)
    Object.assign(deepResult.profile, res.profile)
    deepResult.recommended_positions = (res.recommended_positions || []).map(p => ({
      ...p,
      selected: true,
    }))
    deepResult.search_keywords = res.search_keywords || []
    return res
  }

  // 保存画像
  async function saveProfile(id) {
    await resumeApi.updateProfile(id, {
      profile: deepResult.profile,
      recommended_positions: deepResult.recommended_positions,
      job_preference: { ...jobPreference },
    })
    await fetchList()
  }

  // 上传
  async function upload(file) {
    const res = await resumeApi.upload(file)
    await fetchList()
    return res
  }

  // 删除
  async function remove(id) {
    await resumeApi.delete(id)
    await fetchList()
  }

  return {
    list,
    total,
    loading,
    current,
    deepResult,
    jobPreference,
    fetchList,
    fetchDetail,
    parse,
    deepAnalyze,
    saveProfile,
    upload,
    remove,
  }
})
