# 简历优化系统

针对中小企业（对大龄 IT 从业人员友好）的简历优化系统，根据目标公司 JD 针对性优化简历，并反推面试知识点和攻略。

## 核心功能

| 模块 | 功能 |
|------|------|
| **公司管理** | 公司信息 CRUD，按行业/规模筛选 |
| **JD 管理** | JD 创建、LLM 智能解析（技能要求、大龄友好度分析） |
| **简历管理** | DOCX 上传、LLM 增强解析（技能、工作年限、工作经历提取） |
| **简历优化** | 选择 JD + 简历 → LLM 优化 → 匹配度分析、关键词覆盖、优化建议 |
| **面试攻略** | 知识点清单、高频面试题、答题模板、准备策略、DOCX 导出 |
| **LLM 配置** | 从 OpenClaw 自动导入，支持 MiMo / DeepSeek 切换 |

## 技术栈

| 组件 | 技术 |
|------|------|
| **后端** | Python 3.12 + FastAPI + SQLAlchemy + SQLite |
| **前端** | Vue 3 + Element Plus + Vite |
| **LLM** | MiMo-v2.5 / DeepSeek（OpenAI 兼容接口） |
| **文件存储** | 本地目录 |

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
uv venv .venv --python 3.12
uv pip install -r requirements.txt --python .venv/bin/python
```

### 2. 配置 LLM

从 OpenClaw 导入配置（推荐）：
```bash
cd backend
.venv/bin/python scripts/import_llm_config.py
```

或手动配置：
```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 API Key
```

### 3. 启动服务

```bash
# 方式一：启动脚本
./start.sh

# 方式二：分别启动
# 后端
cd backend && .venv/bin/uvicorn main:app --reload --port 8000

# 前端
cd frontend && npm run dev
```

### 4. 访问

- **前端**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs

## 项目结构

```
resume-optimizer/
├── backend/                    # FastAPI 后端
│   ├── api/                    # API 路由层
│   ├── services/               # 业务逻辑层
│   ├── models/                 # SQLAlchemy 模型
│   ├── schemas/                # Pydantic Schema
│   ├── utils/                  # DOCX 解析/生成
│   ├── scripts/                # 工具脚本
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   └── config.yaml             # LLM 配置
├── frontend/                   # Vue 3 前端
│   └── src/
│       ├── views/              # 页面组件
│       ├── api.js              # API 封装
│       └── router.js           # 路由
├── data/                       # 数据目录
│   ├── db/                     # SQLite 数据库
│   └── files/                  # DOCX 文件
├── docs/                       # 文档
│   └── ARCHITECTURE.md         # 技术架构文档
├── start.sh                    # 启动脚本
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/companies` | 创建公司 |
| GET | `/api/v1/companies` | 公司列表 |
| POST | `/api/v1/jd` | 创建 JD |
| POST | `/api/v1/jd/{id}/parse` | LLM 解析 JD |
| POST | `/api/v1/resume/upload` | 上传简历 |
| POST | `/api/v1/resume/{id}/parse` | LLM 解析简历 |
| POST | `/api/v1/optimization` | 创建优化任务 |
| POST | `/api/v1/optimization/{id}/execute` | 执行优化 |
| GET | `/api/v1/optimization/{id}/download` | 下载优化简历 |
| POST | `/api/v1/interview` | 创建面试攻略 |
| POST | `/api/v1/interview/{id}/generate` | 生成攻略内容 |
| GET | `/api/v1/interview/{id}/download` | 下载攻略文档 |
| GET | `/api/v1/stats/dashboard` | 仪表盘统计 |
| GET | `/api/v1/llm/providers` | LLM Provider 列表 |

完整 API 文档请访问: http://localhost:8000/docs

## 使用流程

```
1. 创建公司 → 2. 添加 JD → 3. 解析 JD（AI 提取技能要求）
                                    ↓
4. 上传简历 → 5. 解析简历（AI 提取技能/经历）→ 6. 创建优化任务
                                                    ↓
                                        7. 执行优化（AI 优化简历）
                                                    ↓
                                    8. 下载优化简历 / 生成面试攻略
```

## 常见问题

### LLM 超时

默认超时 5 分钟。如遇超时，可：
- 换用 DeepSeek（更快）
- 检查网络连接

### 解析结果不完整

- 确保 DOCX 文件格式规范
- 点击「AI 解析」重新提取

## License

MIT
