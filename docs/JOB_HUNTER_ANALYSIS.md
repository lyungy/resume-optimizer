# 求职岗位自动筛选 Skill - 需求与技术分析

> 版本：v1.0 | 日期：2026-05-20

---

## 一、需求概述

### 1.1 业务背景

用户是大龄 IT 从业者（35岁+），需要在多个招聘平台寻找对大龄友好的工作岗位。手动筛选效率低，需要自动化工具帮助：
- 批量搜索符合条件的岗位
- 自动筛选对大龄友好的公司
- 将 JD 导入简历优化系统进行针对性优化

### 1.2 核心需求

| 需求 | 优先级 | 说明 |
|------|--------|------|
| 平台登录 | P0 | 通过 OpenClaw Browser 登录招聘平台 |
| 岗位搜索 | P0 | 按关键词、城市、薪资等条件搜索 |
| 智能筛选 | P0 | 筛选对大龄友好的岗位（无年龄限制、看重经验） |
| JD 导入 | P0 | 将筛选结果导入简历优化系统 |
| 批量操作 | P1 | 支持批量搜索、批量导入 |
| 多平台支持 | P2 | Boss直聘、拉勾、智联招聘等 |

### 1.3 目标用户画像

- 年龄：35岁+
- 职业：IT/互联网（开发、架构、项目管理、产品）
- 工作年限：8年+
- 诉求：找对大龄友好、看重经验的公司

---

## 二、招聘平台分析

### 2.1 主流平台对比

| 平台 | 网址 | 特点 | 大龄友好度 | 技术岗位量 |
|------|------|------|------------|------------|
| **Boss直聘** | zhipin.com | 直聊模式，用户量最大 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **拉勾网** | lagou.com | 互联网垂直招聘 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **智联招聘** | zhaopin.com | 综合类，传统企业多 | ⭐⭐ | ⭐⭐⭐ |
| **猎聘** | liepin.com | 中高端，猎头模式 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **前程无忧** | 51job.com | 综合类，传统企业多 | ⭐⭐ | ⭐⭐⭐ |

### 2.2 推荐优先级

**第一阶段**：Boss直聘（用户量大、岗位多、直聊模式）
**第二阶段**：拉勾网（互联网垂直、大龄友好）
**第三阶段**：猎聘（中高端、看重经验）

### 2.3 Boss直聘 网站结构分析

**搜索 URL 格式**：
```
https://www.zhipin.com/web/geek/job?query={关键词}&city={城市代码}&experience={经验要求}
```

**城市代码**：
- 101010100 = 北京
- 101020100 = 上海
- 101280100 = 广州
- 101280600 = 深圳
- 101030100 = 天津

**经验要求**：
- 108 = 不限
- 101 = 1-3年
- 102 = 3-5年
- 103 = 5-10年
- 104 = 10年以上

**页面结构**：
- 搜索结果列表：`.job-list-box .job-card-wrapper`
- 职位名称：`.job-name`
- 公司名称：`.company-name`
- 薪资范围：`.salary`
- 工作经验：`.tag-list li:nth-child(2)`
- 公司规模：`.tag-list li:nth-child(3)`

---

## 三、技术方案

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Skill                        │
│  ┌─────────────────────────────────────────────────────┐│
│  │              job-hunter (Skill)                     ││
│  │  - SKILL.md (指令定义)                              ││
│  │  - scripts/ (自动化脚本)                            ││
│  └─────────────────────────────────────────────────────┘│
└───────────────────────────┬─────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│OpenClaw      │   │ Browser      │   │ Resume       │
│Browser       │   │ Automation   │   │ Optimizer    │
│(登录/会话)   │   │ (搜索/提取)  │   │ (API导入)    │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 3.2 技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| 浏览器控制 | OpenClaw Browser | 复用已登录会话 |
| 页面操作 | Playwright API | OpenClaw 内置 |
| 数据提取 | DOM 解析 + LLM | 结构化提取 JD |
| 数据导入 | REST API | 调用简历优化系统 |
| 配置管理 | YAML | 搜索条件、筛选规则 |

### 3.3 核心流程

```
用户触发搜索指令
       │
       ▼
OpenClaw Browser 打开招聘网站
       │
       ▼
检查登录状态（已登录则跳过）
       │
       ▼
构造搜索 URL（关键词+城市+经验）
       │
       ▼
遍历搜索结果页面
       │
       ▼
提取职位卡片信息（标题、公司、薪资、经验要求）
       │
       ▼
进入职位详情页
       │
       ▼
提取完整 JD 内容
       │
       ▼
LLM 分析 JD（大龄友好度判断）
       │
       ▼
筛选符合条件的岗位
       │
       ▼
调用简历优化系统 API 导入
       │
       ▼
返回筛选结果给用户
```

---

## 四、Skill 设计

### 4.1 Skill 结构

```
~/.openclaw/skills/job-hunter/
├── SKILL.md                    # Skill 指令定义
├── scripts/
│   ├── search_jobs.py          # 搜索岗位
│   ├── extract_jd.py           # 提取 JD
│   ├── analyze_jd.py           # 分析 JD（大龄友好度）
│   ├── import_to_system.py     # 导入简历优化系统
│   └── config.yaml             # 配置文件
└── templates/
    └── search_params.yaml      # 搜索参数模板
```

### 4.2 SKILL.md 定义

```markdown
# Job Hunter - 求职岗位自动筛选

## 功能
- 在招聘平台搜索符合条件的岗位
- 自动筛选对大龄友好的公司
- 将 JD 导入简历优化系统

## 指令
- `search [平台] [关键词] [城市]` - 搜索岗位
- `filter [条件]` - 筛选岗位
- `import [岗位ID]` - 导入 JD
- `batch-import` - 批量导入

## 使用示例
- search boss Java 上海
- filter senior-friendly
- import all
```

### 4.3 配置文件设计

```yaml
# config.yaml
platforms:
  boss:
    enabled: true
    base_url: "https://www.zhipin.com"
    search_url: "https://www.zhipin.com/web/geek/job"
  
  lagou:
    enabled: false
    base_url: "https://www.lagou.com"
    search_url: "https://www.lagou.com/wn/zhaopin"

search_defaults:
  keywords: ["Java", "架构师", "技术经理", "项目经理"]
  cities: ["101020100"]  # 上海
  experience: "103"  # 5-10年
  
filter_rules:
  senior_friendly:
    # 对大龄友好的信号
    positive_signals:
      - "看重经验"
      - "资深"
      - "高级"
      - "架构"
      - "管理"
      - "不加班"
      - "弹性"
    # 对大龄不友好的信号
    negative_signals:
      - "35岁以下"
      - "年轻团队"
      - "高强度"
      - "996"
      - "应届"
  
  salary_min: 15000  # 最低薪资

resume_optimizer:
  api_base: "http://localhost:8000/api/v1"
  auto_parse: true  # 自动解析 JD
```

---

## 五、关键技术点

### 5.1 浏览器会话复用

OpenClaw Browser 支持会话保持，登录一次后可复用：

```python
# 通过 OpenClaw Browser API 操作
browser.open("https://www.zhipin.com")
# 检查登录状态
snapshot = browser.snapshot()
if "登录" in snapshot:
    # 需要用户手动登录
    notify("请在浏览器中完成登录")
else:
    # 已登录，继续操作
    pass
```

### 5.2 反爬策略

Boss直聘等平台有反爬机制，需要：

1. **控制请求频率**：每次操作间隔 3-5 秒
2. **模拟人工操作**：随机滚动、移动鼠标
3. **使用真实浏览器**：OpenClaw Browser 是真实浏览器
4. **避免批量操作**：分批次进行

### 5.3 JD 提取策略

**方式一：DOM 解析**（推荐）
- 速度快，准确
- 依赖页面结构稳定性
- 需要维护选择器

**方式二：LLM 提取**
- 适应性强
- 速度慢，成本高
- 作为兜底方案

### 5.4 大龄友好度判断

```python
def analyze_senior_friendly(jd_text: str) -> dict:
    """分析 JD 对大龄从业者的友好度"""
    positive_signals = ["看重经验", "资深", "高级", "架构", "管理"]
    negative_signals = ["35岁以下", "年轻团队", "高强度", "996", "应届"]
    
    positive_count = sum(1 for s in positive_signals if s in jd_text)
    negative_count = sum(1 for s in negative_signals if s in jd_text)
    
    score = (positive_count - negative_count + 5) * 10  # 0-100分
    
    return {
        "score": max(0, min(100, score)),
        "positive_signals": [s for s in positive_signals if s in jd_text],
        "negative_signals": [s for s in negative_signals if s in jd_text],
        "friendly": score >= 60,
    }
```

---

## 六、API 对接

### 6.1 简历优化系统 API

```python
# 创建公司
POST /api/v1/companies
{
    "name": "公司名称",
    "industry": "互联网",
    "size": "150-500人"
}

# 创建 JD
POST /api/v1/jd
{
    "company_id": "uuid",
    "title": "Java架构师",
    "raw_text": "JD完整内容",
    "source_url": "https://www.zhipin.com/job_detail/xxx"
}

# 解析 JD
POST /api/v1/jd/{id}/parse
```

### 6.2 数据流转

```
招聘平台 JD
       │
       ▼
Job Hunter Skill (提取+分析)
       │
       ▼
简历优化系统 API (创建公司+JD+解析)
       │
       ▼
用户在简历优化系统中查看
       │
       ▼
选择 JD 进行简历优化
```

---

## 七、开发计划

| 阶段 | 任务 | 工期 | 交付物 |
|------|------|------|--------|
| **Phase 1** | Skill 框架 + Boss直聘搜索 | 2天 | 基础搜索功能 |
| **Phase 2** | JD 提取 + 大龄友好分析 | 2天 | 智能筛选 |
| **Phase 3** | API 对接 + 批量导入 | 2天 | 系统集成 |
| **Phase 4** | 拉勾网支持 | 1天 | 多平台 |
| **Phase 5** | 优化 + 测试 | 1天 | 稳定版本 |
| **合计** | | **8天** | **v1.0** |

---

## 八、风险评估

| 风险 | 等级 | 应对方案 |
|------|------|----------|
| 反爬检测 | 高 | 控制频率、模拟人工、使用真实浏览器 |
| 页面结构变化 | 中 | 选择器维护、LLM 兜底 |
| 登录状态失效 | 中 | 提示用户重新登录 |
| 搜索结果不全 | 低 | 多关键词组合搜索 |
| API 接口变化 | 低 | 简历优化系统是自建系统 |

---

## 九、后续扩展

1. **更多平台**：猎聘、前程无忧、拉勾
2. **智能推荐**：基于简历自动推荐岗位
3. **投递跟踪**：记录投递状态
4. **薪资分析**：市场薪资水平分析
5. **公司调研**：自动收集公司信息（规模、融资、口碑）

---

*文档结束，等待确认后开始开发。*
