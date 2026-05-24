# 简历驱动智能求职 - 技术设计方案

> 版本：v2.0 | 日期：2026-05-24
> 基于 v1.0 方案（docs/RESUME_DRIVEN_MATCHING.md）调整

---

## 一、产品流程

```
┌─────────────────────────────────────────────────────────────────┐
│  侧边栏菜单（调整顺序）                                          │
│                                                                 │
│  📄 智能求职  ← 新增，放在第一位                                  │
│  📊 首页                                                      │
│  🏢 公司管理                                                   │
│  📋 JD 管理                                                    │
│  📁 简历管理                                                   │
│  ✨ 简历优化                                                   │
│  📖 面试攻略                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 智能求职页面流程（4 步）

```
Step 1: 上传简历
┌─────────────────────────────────────────────────────────┐
│  📄 上传简历                                              │
│                                                         │
│  ┌───────────────────────────────────────────────┐      │
│  │                                               │      │
│  │         拖拽或点击上传 DOCX 文件               │      │
│  │                                               │      │
│  └───────────────────────────────────────────────┘      │
│                                                         │
│  已有简历：                                               │
│  ○ 张三_架构师_15年.docx    [使用此简历]                  │
│  ○ 张三_简历_v2.docx        [使用此简历]                  │
│                                                         │
│                              [下一步 →]                  │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
Step 2: AI 深度解析（自动 + 可编辑）
┌─────────────────────────────────────────────────────────┐
│  🧠 AI 深度解析                                           │
│                                                         │
│  ┌── 个人概览 ──────────────────────────────────────┐   │
│  │ 工作年限: 15年  |  最高职位: 技术总监  | 本科/985 │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌── 核心技能（AI 提取，可编辑）──────────────────────┐   │
│  │ [Java] [Spring Boot] [微服务] [Kafka] [Redis]     │   │
│  │ [K8s] [架构设计] [团队管理]  [+ 添加技能]          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌── 行业经验（AI 提取，可编辑）──────────────────────┐   │
│  │ [互联网] [电商] [金融科技]  [+ 添加行业]           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌── AI 推荐岗位（可编辑、增删）─────────────────────┐   │
│  │                                                  │   │
│  │  ✅ 技术总监      匹配度 ████████░░ 85%  [删除]  │   │
│  │  ✅ 架构师        匹配度 ███████░░░ 78%  [删除]  │   │
│  │  ✅ 技术VP        匹配度 ██████░░░░ 72%  [删除]  │   │
│  │  ☐  CTO          匹配度 █████░░░░░ 65%  [删除]  │   │
│  │  ☐  首席架构师    匹配度 █████░░░░░ 62%  [删除]  │   │
│  │                                                  │   │
│  │  [+ 添加自定义岗位]                               │   │
│  │                                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌── 求职偏好（用户填写）────────────────────────────┐   │
│  │ 期望城市: [上海 ▾]                                │   │
│  │ 期望薪资: [40] ~ [60] K                          │   │
│  │ 接受远程: [是 ▾]                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  [← 上一步]                          [开始搜索 →]       │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
Step 3: 搜索 + 匹配（自动执行，显示进度）
┌─────────────────────────────────────────────────────────┐
│  🔍 搜索匹配中...                                         │
│                                                         │
│  ✅ 搜索 "技术总监" 上海 ... 找到 15 个岗位               │
│  ✅ 搜索 "架构师" 上海 ... 找到 20 个岗位                 │
│  ⏳ 搜索 "技术VP" 上海 ... 进行中                        │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━░░░░░░░░ 60%                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
Step 4: 结果列表（多维匹配 + 操作）
┌─────────────────────────────────────────────────────────┐
│  📊 匹配结果  共 35 个岗位                                 │
│                                                         │
│  排序: [综合匹配度 ▾]  筛选: [最低分 60 ▾]                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ #1  技术总监 - XX科技                             │   │
│  │     40-60K · 上海 · 互联网                        │   │
│  │     综合: 88分                                    │   │
│  │     技能 ████████░░ 80%  经验 ██████████ 100%    │   │
│  │     薪资 ████████░░ 80%  职级 ██████████ 100%    │   │
│  │     年龄 ████████░░ 80%  行业 ██████████ 100%    │   │
│  │     [查看详情] [导入系统] [查看JD]                 │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ #2  架构师 - YY互联网                             │   │
│  │     35-55K · 上海 · 金融科技                      │   │
│  │     综合: 82分                                    │   │
│  │     ...                                          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  [批量导入选中岗位]  [重新搜索]                           │
└─────────────────────────────────────────────────────────┘
```

---

## 二、后端设计

### 2.1 新增 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/resume/{id}/deep-analyze` | 深度解析简历，返回画像+推荐岗位 |
| `PUT` | `/api/v1/resume/{id}/profile` | 更新求职画像（用户编辑后保存） |
| `POST` | `/api/v1/collector/search-match` | 基于画像搜索+匹配 |

### 2.2 深度解析 API 设计

**请求**：`POST /api/v1/resume/{id}/deep-analyze`

**响应**：

```json
{
  "resume_id": "uuid",
  "profile": {
    "hard_skills": {
      "languages": ["Java", "Python"],
      "frameworks": ["Spring Boot", "FastAPI"],
      "middleware": ["Kafka", "Redis", "ES"],
      "architecture": ["微服务", "DDD", "分布式"],
      "devops": ["K8s", "Docker"],
      "databases": ["MySQL", "PostgreSQL"]
    },
    "soft_skills": ["团队管理", "架构设计", "技术选型"],
    "experience_profile": {
      "total_years": 15,
      "highest_title": "技术总监",
      "management_scale": "20人",
      "industries": ["互联网", "电商"],
      "company_sizes": ["大厂", "中型"]
    },
    "education": {
      "degree": "本科",
      "major": "计算机科学",
      "school_tier": "985"
    },
    "project_highlights": [
      {
        "name": "XX平台架构重构",
        "tech_stack": ["Spring Cloud", "Kafka"],
        "scale": "日活百万",
        "achievement": "可用性99.99%"
      }
    ]
  },
  "recommended_positions": [
    {
      "title": "技术总监",
      "match_score": 85,
      "match_reasons": ["15年经验匹配", "有20人管理经验", "互联网行业背景"],
      "selected": true
    },
    {
      "title": "架构师",
      "match_score": 78,
      "match_reasons": ["微服务架构经验", "Spring Boot技术栈"],
      "selected": true
    },
    {
      "title": "技术VP",
      "match_score": 72,
      "match_reasons": ["总监级管理经验", "大型项目经验"],
      "selected": true
    }
  ],
  "search_keywords": ["技术总监", "架构师", "技术VP", "首席架构师"]
}
```

### 2.3 LLM Prompt 设计

深度解析使用专门的 Prompt，要求 LLM 输出结构化 JSON：

```
你是资深职业规划师。根据以下简历内容，完成：

1. 提取硬性技能（分类：语言/框架/中间件/架构/运维/数据库）
2. 提取软技能
3. 分析经验画像（年限/最高职位/管理规模/行业/公司规模）
4. 提取教育背景
5. 提取项目亮点（技术栈/规模/成果）
6. 推荐 5-8 个适合的职业岗位，每个给出匹配度百分比和匹配理由

简历内容：
{resume_text}

输出 JSON 格式，不要额外解释。
```

### 2.4 搜索匹配 API 设计

**请求**：`POST /api/v1/collector/search-match`

```json
{
  "resume_id": "uuid",
  "selected_positions": ["技术总监", "架构师"],
  "city": "上海",
  "salary_min": 40000,
  "salary_max": 60000,
  "limit_per_keyword": 20
}
```

**处理流程**：

```
1. 读取简历画像
2. 遍历 selected_positions，每个作为关键词搜索
3. 对每个搜索结果，计算多维匹配分
4. 按总分排序返回
```

**响应**：

```json
{
  "total": 35,
  "jobs": [
    {
      "title": "技术总监",
      "company_name": "XX科技",
      "salary": "40-60K",
      "location": "上海",
      "url": "https://...",
      "total_score": 88,
      "dimension_scores": {
        "skill_match": {"score": 28, "rate": 80, "matched": ["Java", "微服务"], "missing": ["Go"]},
        "experience_match": {"score": 20, "detail": "15年经验完美匹配"},
        "salary_match": {"score": 12, "detail": "40-60K匹配期望"},
        "title_match": {"score": 15, "detail": "技术总监完美匹配"},
        "age_friendly": {"score": 8, "detail": "经验10年+，大龄友好"},
        "industry_match": {"score": 5, "detail": "互联网行业匹配"}
      },
      "recommendation": "强烈推荐",
      "reasons": ["技能匹配80%", "薪资匹配", "职位匹配"]
    }
  ]
}
```

---

## 三、前端设计

### 3.1 路由调整

```javascript
const routes = [
  { path: '/smart-job', name: 'SmartJob', component: () => import('@/views/SmartJob.vue') },  // 🆕 放第一位
  { path: '/', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/company', name: 'Company', component: () => import('@/views/Company.vue') },
  { path: '/jd', name: 'JD', component: () => import('@/views/JD.vue') },
  { path: '/resume', name: 'Resume', component: () => import('@/views/Resume.vue') },
  { path: '/optimization', name: 'Optimization', component: () => import('@/views/Optimization.vue') },
  { path: '/interview', name: 'Interview', component: () => import('@/views/Interview.vue') },
]
```

### 3.2 侧边栏菜单调整

```html
<el-menu-item index="/smart-job">
  <el-icon><Position /></el-icon>
  <span>智能求职</span>
</el-menu-item>
<el-menu-item index="/">
  <el-icon><DataBoard /></el-icon>
  <span>首页</span>
</el-menu-item>
<!-- 其余不变 -->
```

### 3.3 SmartJob.vue 组件结构

```
SmartJob.vue
├── Step 1: UploadStep.vue        ← 上传简历 / 选择已有简历
├── Step 2: AnalysisStep.vue      ← AI解析结果 + 可编辑
├── Step 3: SearchStep.vue        ← 搜索进度
└── Step 4: ResultStep.vue        ← 匹配结果列表
```

使用 Element Plus 的 `el-steps` 组件实现步骤条。

### 3.4 AnalysisStep.vue 核心交互

**AI 解析结果展示区**：

```html
<!-- 个人概览（只读） -->
<el-descriptions>
  <el-descriptions-item label="工作年限">{{ profile.experience_profile.total_years }}年</el-descriptions-item>
  <el-descriptions-item label="最高职位">{{ profile.experience_profile.highest_title }}</el-descriptions-item>
</el-descriptions>

<!-- 核心技能（可编辑标签） -->
<el-divider>核心技能</el-divider>
<el-tag v-for="skill in profile.all_skills" :key="skill" closable @close="removeSkill(skill)">
  {{ skill }}
</el-tag>
<el-input v-if="addingSkill" v-model="newSkill" @keyup.enter="addSkill" />
<el-button v-else @click="addingSkill = true">+ 添加技能</el-button>

<!-- AI 推荐岗位（可勾选、可删除、可新增） -->
<el-divider>AI 推荐岗位</el-divider>
<div v-for="pos in recommendedPositions" :key="pos.title">
  <el-checkbox v-model="pos.selected" />
  <span>{{ pos.title }}</span>
  <el-progress :percentage="pos.match_score" />
  <el-button text @click="removePosition(pos)">删除</el-button>
</div>
<el-button @click="showAddPosition = true">+ 添加自定义岗位</el-button>

<!-- 求职偏好（用户填写） -->
<el-divider>求职偏好</el-divider>
<el-form>
  <el-form-item label="期望城市">
    <el-select v-model="preference.city">
      <el-option label="上海" value="上海" />
      <el-option label="北京" value="北京" />
      <el-option label="杭州" value="杭州" />
      <el-option label="深圳" value="深圳" />
    </el-select>
  </el-form-item>
  <el-form-item label="期望薪资">
    <el-input-number v-model="preference.salary_min" :step="5000" /> K ~
    <el-input-number v-model="preference.salary_max" :step="5000" /> K
  </el-form-item>
</el-form>
```

---

## 四、数据库变更

### 4.1 Resume 表新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `profile` | JSON | 求职画像（深度解析结果） |
| `recommended_positions` | JSON | AI 推荐岗位列表 |
| `job_preference` | JSON | 用户求职偏好 |

```sql
ALTER TABLE resumes ADD COLUMN profile JSON;
ALTER TABLE resumes ADD COLUMN recommended_positions JSON;
ALTER TABLE resumes ADD COLUMN job_preference JSON;
```

### 4.2 无需新增表

所有数据存在 Resume 表中，不新增表。

---

## 五、文件变更清单

### 5.1 后端

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/api/resume.py` | 🔧 新增 | 深度解析 + 画像更新 API |
| `backend/api/collector.py` | 🆕 新增 | 搜索匹配 API |
| `backend/schemas/resume.py` | 🔧 扩展 | 新增画像相关 Schema |
| `backend/models/resume.py` | 🔧 扩展 | 新增 3 个 JSON 字段 |
| `backend/services/resume_service.py` | 🔧 扩展 | 新增深度解析方法 |
| `backend/services/llm/prompts/resume_deep_analyzer.py` | 🆕 新增 | 深度解析 Prompt |

### 5.2 前端

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/views/SmartJob.vue` | 🆕 新增 | 智能求职主页面 |
| `frontend/src/views/smart-job/UploadStep.vue` | 🆕 新增 | Step 1 上传简历 |
| `frontend/src/views/smart-job/AnalysisStep.vue` | 🆕 新增 | Step 2 深度解析（可编辑） |
| `frontend/src/views/smart-job/SearchStep.vue` | 🆕 新增 | Step 3 搜索进度 |
| `frontend/src/views/smart-job/ResultStep.vue` | 🆕 新增 | Step 4 匹配结果 |
| `frontend/src/api.js` | 🔧 扩展 | 新增 collector API |
| `frontend/src/router.js` | 🔧 调整 | 新增路由，调整顺序 |
| `frontend/src/App.vue` | 🔧 调整 | 菜单顺序调整 |

### 5.3 Collector 模块

| 文件 | 操作 | 说明 |
|------|------|------|
| `collector/profile.py` | 🆕 新增 | 求职画像生成 + 搜索策略推导 |
| `collector/matcher.py` | 🆕 新增 | 多维匹配引擎 |
| `collector/__main__.py` | 🔧 扩展 | 新增 profile/match 子命令 |

---

## 六、开发计划

| 阶段 | 任务 | 预计工时 |
|------|------|----------|
| 1 | 后端：简历模型扩展 + 深度解析 API | 3h |
| 2 | 后端：搜索匹配 API（collector 集成） | 2h |
| 3 | 前端：SmartJob.vue 四步流程 | 4h |
| 4 | 前端：AnalysisStep 可编辑交互 | 2h |
| 5 | 前端：ResultStep 多维匹配展示 | 2h |
| 6 | 联调测试 | 2h |
| **合计** | | **15h** |

---

## 七、与现有功能的关系

| 现有功能 | 影响 |
|----------|------|
| 首页 Dashboard | 不变 |
| 公司/JD/简历/优化/面试 | 不变 |
| `collector search` | 保留，泛搜模式 |
| `collector match` | 🆕 新增，简历驱动模式 |
| 简历解析 | 扩展（增加深度解析） |

**两种模式并存**：
- **智能求职**（前端）→ 上传简历 → AI 解析 → 搜索匹配
- **命令行采集**（CLI）→ `collector search` 泛搜 / `collector match` 简历驱动

---

*方案待确认。*
