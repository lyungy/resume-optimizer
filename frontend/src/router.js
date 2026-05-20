import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
  },
  {
    path: '/company',
    name: 'Company',
    component: () => import('@/views/Company.vue'),
  },
  {
    path: '/jd',
    name: 'JD',
    component: () => import('@/views/JD.vue'),
  },
  {
    path: '/resume',
    name: 'Resume',
    component: () => import('@/views/Resume.vue'),
  },
  {
    path: '/optimization',
    name: 'Optimization',
    component: () => import('@/views/Optimization.vue'),
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('@/views/Interview.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
