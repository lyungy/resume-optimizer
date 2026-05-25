<template>
  <el-container class="app-container">
    <el-aside width="200px" class="app-aside">
      <div class="logo">
        <h2>简历优化系统</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="aside-menu"
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/resume">
          <el-icon><Files /></el-icon>
          <span>简历管理</span>
        </el-menu-item>
        <el-menu-item index="/company">
          <el-icon><OfficeBuilding /></el-icon>
          <span>公司管理</span>
        </el-menu-item>
        <el-menu-item index="/jd">
          <el-icon><Document /></el-icon>
          <span>JD 管理</span>
        </el-menu-item>
        <el-menu-item index="/optimization">
          <el-icon><MagicStick /></el-icon>
          <span>简历优化</span>
        </el-menu-item>
        <el-menu-item index="/interview">
          <el-icon><Reading /></el-icon>
          <span>面试攻略</span>
        </el-menu-item>
        <el-menu-item index="/llm-logs">
          <el-icon><Monitor /></el-icon>
          <span>LLM 日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <span>{{ currentTitle }}</span>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const activeMenu = computed(() => route.path)

const titleMap = {
  '/': '仪表盘',
  '/resume': '简历管理',
  '/company': '公司管理',
  '/jd': 'JD 管理',
  '/optimization': '简历优化',
  '/interview': '面试攻略',
  '/llm-logs': 'LLM 日志',
}

const currentTitle = computed(() => titleMap[route.path] || '简历优化系统')
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

.app-container {
  height: 100vh;
}

.app-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo h2 {
  color: #fff;
  font-size: 16px;
}

.aside-menu {
  border-right: none;
  background-color: #304156;
}

.aside-menu .el-menu-item {
  color: #bfcbd9;
}

.aside-menu .el-menu-item:hover,
.aside-menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
