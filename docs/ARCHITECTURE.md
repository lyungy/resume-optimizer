# 简历优化系统 - 技术架构文档

> 版本：v1.0 | 更新日期：2026-05-20

---

## 一、系统概述

### 1.1 项目定位

针对中小企业（对大龄 IT 从业人员友好）的简历优化系统，核心能力：
- 根据目标公司 JD 针对性优化简历
- 反推面试知识点和攻略
- 支持批量管理多家公司

### 1.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| Python | CPython | 3.12 | brew 已安装，稳定 |
| Web 框架 | FastAPI | 0.115 | 异步高性能，自动 OpenAPI 文档 |
| ORM | SQLAlchemy | 2.0 | 成熟稳定，类型支持好 |
| 数据库 | SQLite | - | 零运维，前期数据量小 |
| 前端框架 | Vue 3 | 3.x | 轻量级，学习成本低 |
| UI 组件 | Element Plus | - | 企业级中后台组件库 |
| 构建工具 | Vite | 8.x | 快速 HMR |
| LLM | OpenAI 兼容 API | - | 统一接口，支持 MiMo/DeepSeek |
| 文档处理 | python-docx | 1.1 | DOCX 读写 |

---

## 二、目录结构

```
resume-optimizer/
├── backend/                        # 后端服务
│   ├── api/                        # API 路由层（仅做参数校验和响应）
│   │   ├── __init__.py
│   │   ├── company.py              # 公司 CRUD
│   │   ├── jd.py                   # JD CRUD + 解析
│   │   ├── resume.py               # 简历上传 + 解析
│   │   ├── optimization.py         # 简历优化任务
│   │   ├── interview.py            # 面试攻略
│   │   ├── llm.py                  # LLM 配置查询
│   │   └── stats.py                # 统计仪表盘
│   │
│   ├── services/                   # 业务逻辑层（核心）
│   │   ├── __init__.py
│   │   ├── jd_service.py           # JD 解析服务
│   │   ├── resume_service.py       # 简历解析服务
│   │   ├── optimization_service.py # 简历优化引擎
│   │   ├── interview_service.py    # 面试攻略生成
│   │   └── llm/                    # LLM 适配层
│   │       ├── __init__.py
│   │       ├── config_reader.py    # 读取 OpenClaw 配置
│   │       ├── client.py           # OpenAI 兼容客户端
│   │       └── prompts/            # Prompt 模板
│   │           ├── __init__.py
│   │           ├── jd_parser.py    # JD 解析 Prompt
│   │           ├── resume_parser.py # 简历解析 Prompt
│   │           ├── resume_optimizer.py # 简历优化 Prompt
│   │           └── interview_guide.py # 面试攻略 Prompt
│   │
│   ├── models/                     # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── database.py             # 数据库连接
│   │   ├── base.py                 # 基类（Base + TimestampMixin）
│   │   ├── company.py              # 公司模型
│   │   ├── jd.py                   # JD 模型
│   │   ├── resume.py               # 简历模型
│   │   ├── optimization.py         # 优化任务模型
│   │   └── interview.py            # 面试攻略模型
│   │
│   ├── schemas/                    # Pydantic 请求/响应 Schema
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── jd.py
│   │   ├── resume.py
│   │   ├── optimization.py
│   │   └── interview.py
│   │
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── docx_parser.py          # DOCX 解析（段落 + 表格）
│   │   └── docx_writer.py          # DOCX 生成（简历/攻略导出）
│   │
│   ├── scripts/                    # 工具脚本
│   │   └── import_llm_config.py    # 从 OpenClaw 导入 LLM 配置
│   │
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 配置管理
│   └── config.yaml                 # LLM 配置文件
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   │   ├── Dashboard.vue       # 仪表盘
│   │   │   ├── Company.vue         # 公司管理
│   │   │   ├── JD.vue              # JD 管理
│   │   │   ├── Resume.vue          # 简历管理
│   │   │   ├── Optimization.vue    # 简历优化
│   │   │   └── Interview.vue       # 面试攻略
│   │   ├── api.js                  # API 封装（axios）
│   │   ├── router.js               # 路由配置
│   │   ├── main.js                 # 入口
│   │   └── App.vue                 # 布局
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── data/                           # 数据目录
│   ├── db/
│   │   └── resume_optimizer.db     # SQLite 数据库
│   └── files/
│       ├── resumes/                # 上传的简历文件
│       └── optimized/              # 优化后的文件
│
├── docs/                           # 文档
│   └── ARCHITECTURE.md             # 本文件
│
├── start.sh                        # 启动脚本
└── README.md
```

---

## 三、架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                      │
│  Company | JD | Resume | Optimization | Interview        │
└───────────────────────┬─────────────────────────────────┘
                        │ REST API (axios)
┌───────────────────────▼─────────────────────────────────┐
│                  API Layer (FastAPI)                      │
│  参数校验 → 调用 Service → 返回响应                       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                Services Layer (业务逻辑)                  │
│  JD Service | Resume Service | Optimization Service      │
│                  Interview Service                        │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  LLM Service │ │  DOCX Utils  │ │   Database   │
│  (AI 调用)   │ │  (文件处理)  │ │   (SQLite)   │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 3.2 职责划分

| 层级 | 职责 | 不做什么 |
|------|------|----------|
| **API** | 参数校验、调用 Service、返回响应 | 不写业务逻辑 |
| **Service** | 业务逻辑、数据组装、AI 调用 | 不处理 HTTP |
| **Model** | 数据结构定义、ORM 映射 | 不含业务逻辑 |
| **Schema** | 请求/响应数据结构 | 不含数据库操作 |
| **Utils** | 通用工具函数 | 不含业务逻辑 |

---

## 四、数据模型

### 4.1 ER 图

```
┌──────────────┐       ┌──────────────┐
│   Company    │ 1   N │      JD      │
│──────────────│───────│──────────────│
│ id (PK)      │       │ id (PK)      │
│ name         │       │ company_id   │
│ industry     │       │ title        │
│ size         │       │ raw_text     │
│ website      │       │ is_parsed    │
│ notes        │       │ hard_skills  │
└──────────────┘       │ soft_skills  │
                       │ key_keywords │
                       │ senior_friendly│
                       └──────┬───────┘
                              │
                              │ N:M (通过 Optimization)
                              ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Resume     │ 1   N │ Optimization │ 1   1 │InterviewGuide│
│──────────────│───────│──────────────│───────│──────────────│
│ id (PK)      │       │ id (PK)      │       │ id (PK)      │
│ name         │       │ jd_id (FK)   │       │optimization_id│
│ file_path    │       │ resume_id(FK)│       │knowledge_pts │
│ is_parsed    │       │ status       │       │questions     │
│ skills       │       │ match_score  │       │strategy      │
│ experience_y │       │ result       │       │docx_path     │
│ work_exp     │       │ docx_path    │       └──────────────┘
│ projects     │       └──────────────┘
└──────────────┘
```

### 4.2 表结构

**companies**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | UUID 主键 |
| name | VARCHAR(200) | 公司名称 |
| industry | VARCHAR(100) | 行业 |
| size | VARCHAR(50) | 规模 |
| website | VARCHAR(500) | 官网 |
| notes | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**job_descriptions**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | UUID 主键 |
| company_id | VARCHAR(36) | 外键→companies |
| title | VARCHAR(200) | 职位名称 |
| raw_text | TEXT | 原始 JD 文本 |
| is_parsed | BOOLEAN | 是否已解析 |
| hard_skills | JSON | 硬性技能 |
| soft_skills | JSON | 软性技能 |
| key_keywords | JSON | ATS 关键词 |
| difficulty_level | VARCHAR(20) | 难度级别 |
| senior_friendly | BOOLEAN | 大龄友好度 |

**resumes**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | UUID 主键 |
| name | VARCHAR(200) | 简历名称 |
| original_file_path | VARCHAR(500) | 文件路径 |
| is_parsed | BOOLEAN | 是否已解析 |
| skills | JSON | 技能标签 |
| experience_years | INTEGER | 工作年限 |
| education | JSON | 教育经历 |
| work_experience | JSON | 工作经历 |
| projects | JSON | 项目经历 |

**optimizations**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | UUID 主键 |
| jd_id | VARCHAR(36) | 外键→job_descriptions |
| resume_id | VARCHAR(36) | 外键→resumes |
| llm_provider | VARCHAR(50) | LLM Provider |
| llm_model | VARCHAR(100) | LLM 模型 |
| status | VARCHAR(20) | 状态 |
| match_score | FLOAT | 匹配度 |
| keyword_coverage | JSON | 关键词覆盖 |
| optimization_result | JSON | 优化结果 |
| suggestions | JSON | 优化建议 |
| optimized_docx_path | VARCHAR(500) | 导出文件路径 |

**interview_guides**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | UUID 主键 |
| optimization_id | VARCHAR(36) | 外键→optimizations |
| knowledge_points | JSON | 知识点清单 |
| high_frequency_questions | JSON | 高频面试题 |
| preparation_strategy | JSON | 准备策略 |
| company_research | JSON | 公司调研 |
| export_docx_path | VARCHAR(500) | 导出文件路径 |

---

## 五、LLM 适配层

### 5.1 设计思路

```
config.yaml (LLM 配置)
       │
       ▼
┌──────────────────┐
│  ConfigReader    │  读取 OpenClaw 配置或本地配置
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   LLMClient      │  OpenAI 兼容客户端
│   - chat()       │  同步调用
│   - chat_json()  │  JSON 格式输出
│   - chat_stream()│  流式输出
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Prompts        │  Prompt 模板管理
│   - jd_parser    │  JD 解析
│   - resume_parser│  简历解析
│   - optimizer    │  简历优化
│   - interview    │  面试攻略
└──────────────────┘
```

### 5.2 配置管理

```yaml
# config.yaml
llm:
  default_provider: xiaomi-coding
  providers:
    xiaomi-coding:
      name: xiaomi-coding
      base_url: https://token-plan-cn.xiaomimimo.com/v1
      api_key: ***
      models:
        - id: mimo-v2.5-pro
          name: MiMo V2.5 Pro
          is_default: true
        - id: mimo-v2.5
          name: MiMo V2.5
    deepseek:
      name: deepseek
      base_url: https://api.deepseek.com
      api_key: ***
      models:
        - id: deepseek-v4-flash
          name: DeepSeek V4 Flash
```

### 5.3 导入脚本

```bash
# 从 OpenClaw 自动导入 LLM 配置
.venv/bin/python backend/scripts/import_llm_config.py
```

读取 `~/.openclaw/openclaw.json` 中的 `models.providers` 配置，写入 `config.yaml`。

---

## 六、核心流程

### 6.1 JD 解析流程

```
用户输入 JD 文本
       │
       ▼
创建 JD 记录 (is_parsed=false)
       │
       ▼
调用 LLM (jd_parser prompt)
       │
       ▼
解析 JSON 结果
       │
       ▼
更新 JD 记录:
  - hard_skills
  - soft_skills
  - key_keywords
  - difficulty_level
  - senior_friendly
  - senior_friendly_signals
  - concern_signals
```

### 6.2 简历解析流程

```
用户上传 DOCX
       │
       ▼
保存文件 + 基础解析 (is_parsed=false)
       │
       ▼
用户点击「AI 解析」
       │
       ▼
DOCX 解析器提取文本 (段落 + 表格)
       │
       ▼
调用 LLM (resume_parser prompt)
       │
       ▼
解析 JSON 结果
       │
       ▼
更新简历记录:
  - skills
  - experience_years
  - education
  - work_experience
  - projects
```

### 6.3 简历优化流程

```
用户选择 JD + 简历
       │
       ▼
创建优化任务 (status=pending)
       │
       ▼
用户点击「执行优化」
       │
       ▼
获取 JD 结构化数据 + 简历文本
       │
       ▼
调用 LLM (resume_optimizer prompt)
       │
       ▼
解析 JSON 结果
       │
       ▼
更新优化任务:
  - match_score
  - keyword_coverage
  - suggestions
  - ats_tips
  - optimization_result
       │
       ▼
生成优化简历 DOCX
```

### 6.4 面试攻略生成流程

```
优化任务完成
       │
       ▼
用户点击「生成攻略」
       │
       ▼
创建攻略记录
       │
       ▼
获取 JD + 优化结果摘要
       │
       ▼
调用 LLM (interview_guide prompt)
       │
       ▼
解析 JSON 结果
       │
       ▼
更新攻略记录:
  - knowledge_points
  - high_frequency_questions
  - preparation_strategy
  - company_research
       │
       ▼
生成攻略 DOCX
```

---

## 七、DOCX 处理

### 7.1 解析器 (docx_parser.py)

**核心能力**：
- 按文档顺序遍历段落和表格
- 表格内容完整提取（不截断）
- 输出结构化 JSON

**输出格式**：
```json
{
  "text": "完整文本（段落+表格拼接）",
  "paragraphs": ["段落1", "段落2"],
  "tables": [
    {
      "headers": ["列1", "列2"],
      "rows": [["值1", "值2"]],
      "formatted_text": "格式化后的表格文本"
    }
  ],
  "sections": {"工作经历": "...", "教育经历": "..."}
}
```

### 7.2 生成器 (docx_writer.py)

**支持导出**：
- 优化后的简历 DOCX
- 面试攻略 DOCX

**格式化**：
- 标题居中
- 分节标题
- 列表项
- 表格

---

## 八、前端设计

### 8.1 页面结构

```
┌─────────────────────────────────────────────────────────┐
│  Logo    首页   公司   JD   简历   优化   面试攻略        │
└─────────────────────────────────────────────────────────┘
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  页面内容区                       │   │
│  │  - 表格列表                                      │   │
│  │  - 搜索筛选                                      │   │
│  │  - 操作按钮                                      │   │
│  │  - 分页                                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 8.2 状态管理

使用 Pinia，但当前版本状态简单，主要通过组件内 ref 管理。

### 8.3 API 封装

```javascript
// api.js
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000,  // 5分钟（LLM 调用耗时）
})

// 各模块 API
export const companyApi = { ... }
export const jdApi = { ... }
export const resumeApi = { ... }
export const optimizationApi = { ... }
export const interviewApi = { ... }
export const llmApi = { ... }
export const statsApi = { ... }
```

---

## 九、配置说明

### 9.1 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | sqlite:///... | 数据库连接 |
| FILES_DIR | ./data/files | 文件存储目录 |
| BACKEND_HOST | 0.0.0.0 | 后端监听地址 |
| BACKEND_PORT | 8000 | 后端端口 |
| DEBUG | false | 调试模式 |

### 9.2 LLM 配置

配置文件：`backend/config.yaml`

支持的 Provider：
- **xiaomi-coding**：MiMo 模型（默认）
- **deepseek**：DeepSeek 模型

切换方式：
1. 前端创建优化任务时选择
2. 修改 `config.yaml` 中的 `default_provider`

---

## 十、部署说明

### 10.1 开发环境

```bash
# 安装依赖
cd resume-optimizer
uv venv .venv --python 3.12
uv pip install -r backend/requirements.txt --python .venv/bin/python

# 后端
.venv/bin/uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 10.2 生产环境

```bash
# 后端
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端
cd frontend
npm run build
# 将 dist/ 部署到 Nginx
```

### 10.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 300s;
    }
}
```

---

## 十一、扩展指南

### 11.1 新增 LLM Provider

1. 在 `config.yaml` 中添加 Provider 配置
2. 无需修改代码，自动读取

### 11.2 新增简历格式

1. 在 `utils/` 中实现新的 Parser
2. 在 `resume_service.py` 中注册

### 11.3 新增导出格式

1. 在 `utils/` 中实现新的 Writer
2. 在对应 Service 中调用

### 11.4 新增页面

1. 在 `frontend/src/views/` 中创建组件
2. 在 `router.js` 中添加路由
3. 在 `api.js` 中添加 API 封装

---

## 十二、已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| LLM 调用超时 | 已缓解 | 超时设为 5 分钟 |
| 复杂 DOCX 解析 | 已优化 | 表格内容完整提取 |
| 解析结果不完整 | 已优化 | 改进 Prompt，增加 token |

---

## 十三、变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-20 | v1.0 | 初始版本，完成核心功能 |
