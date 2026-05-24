# Job Hunter - 求职岗位自动筛选 Skill

> 版本：v1.0 | 日期：2026-05-20

---

## 一、需求概述

### 1.1 业务背景

用户是大龄 IT 从业者（35岁+），需要在多个招聘平台寻找对大龄友好的工作岗位。手动筛选效率低，需要自动化工具帮助。

### 1.2 核心需求

| 需求 | 优先级 | 说明 |
|------|--------|------|
| 多平台支持 | P0 | Boss直聘、拉勾、猎聘等 |
| 岗位搜索 | P0 | 按关键词、城市、经验等条件搜索 |
| 智能筛选 | P0 | 筛选对大龄友好的岗位 |
| JD 导入 | P0 | 将筛选结果导入简历优化系统 |
| 可配置 | P0 | 搜索条件、筛选规则可配置 |
| 批量操作 | P1 | 支持批量搜索、批量导入 |
| 增量搜索 | P2 | 记录已搜索岗位，避免重复 |

### 1.3 配置项

```yaml
# 搜索条件
search:
  keywords: ["技术经理", "Java架构师", "项目经理"]  # 多关键词
  cities: ["上海"]  # 城市
  experience: "5-10年"  # 经验要求
  salary_min: 15000  # 最低薪资

# 平台配置
platforms:
  boss: { enabled: true }
  lagou: { enabled: false }
  liepin: { enabled: false }
```

---

## 二、Skill 结构

```
~/.openclaw/skills/job-hunter/
├── SKILL.md                        # Skill 指令定义
├── config.yaml                     # 配置文件（搜索条件、平台、筛选规则）
├── scripts/
│   ├── __init__.py
│   ├── main.py                     # 主入口
│   ├── browser.py                  # 浏览器操作封装
│   ├── platforms/                   # 平台适配层
│   │   ├── __init__.py
│   │   ├── base.py                 # 平台基类
│   │   ├── boss.py                 # Boss直聘
│   │   ├── lagou.py                # 拉勾（预留）
│   │   └── liepin.py               # 猎聘（预留）
│   ├── analyzer.py                 # JD 分析（大龄友好度）
│   ├── importer.py                 # 导入简历优化系统
│   └── utils.py                    # 工具函数
└── data/
    └── search_history.json         # 搜索历史（增量去重）
```

### 2.1 SKILL.md

```markdown
---
name: job-hunter
description: 求职岗位自动筛选。在招聘平台搜索岗位，智能筛选对大龄友好的公司，导入简历优化系统。Use when: 搜索工作、找工作、求职、筛选岗位、导入JD。
---

# Job Hunter - 求职岗位自动筛选

通过 OpenClaw Browser 登录招聘平台，自动搜索筛选对大龄友好的岗位，导入简历优化系统。

## 前置条件

1. OpenClaw Browser 已启动
2. 浏览器中已登录目标招聘平台（Boss直聘等）
3. 简历优化系统已启动（localhost:8000）

## 使用方式

```bash
# 搜索岗位（使用默认配置）
python3 scripts/main.py search

# 指定关键词和城市
python3 scripts/main.py search -k "技术经理" -k "架构师" -c 上海

# 搜索并自动导入
python3 scripts/main.py search --import

# 仅导入已有结果
python3 scripts/main.py import

# 查看搜索历史
python3 scripts/main.py history

# 清空搜索历史
python3 scripts/main.py clear-history
```

## CLI 参数

### search 子命令

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--keyword` | `-k` | ❌ | 搜索关键词（可多次指定） |
| `--city` | `-c` | ❌ | 城市名称 |
| `--platform` | `-p` | ❌ | 平台（boss/lagou/liepin） |
| `--import` | `-i` | ❌ | 搜索后自动导入系统 |
| `--limit` | `-l` | ❌ | 最大搜索数量（默认20） |
| `--min-score` | `-s` | ❌ | 最低友好度分数（默认60） |
| `--max-import` | `-m` | ❌ | 最多导入数量（默认50） |

### import 子命令

| 参数 | 缩写 | 必填 | 说明 |
|------|------|------|------|
| `--file` | `-f` | ❌ | 指定导入文件 |
| `--ids` | | ❌ | 指定岗位ID导入 |

## 输出示例

```
🔍 搜索条件：技术经理 | 上海 | Boss直聘
📊 找到 25 个岗位

  #   职位                公司              薪资        友好度  状态
  1   技术经理            XX科技            25-40K      85分    ✅ 已导入
  2   高级架构师          YY网络            30-50K      78分    ✅ 已导入
  3   Java开发            ZZ信息            15-25K      45分    ❌ 低于阈值

✅ 成功导入 18 个岗位到简历优化系统
```
```

### 2.2 config.yaml

```yaml
# Job Hunter 配置文件

# 搜索条件
search:
  # 默认关键词（支持多个）
  keywords:
    - "技术经理"
    - "Java架构师"
    - "项目经理"
    - "技术总监"
  
  # 默认城市（支持多个）
  cities:
    - "上海"
    # - "北京"
    # - "深圳"
  
  # 经验要求
  experience: "5-10年"
  
  # 最低薪资
  salary_min: 15000
  
  # 每次搜索最大数量
  limit: 20

# 导入配置
import:
  # 最多导入 JD 数量
  max_count: 50
  
  # 导入后自动解析
  auto_parse: true
  
  # 重复检测（基于 title + company）
  skip_duplicates: true
  
  # 导入间隔（秒，防 API 压力）
  interval: 1

# 平台配置
platforms:
  boss:
    enabled: true
    name: "Boss直聘"
    base_url: "https://www.zhipin.com"
    search_url: "https://www.zhipin.com/web/geek/job"
    # 城市代码映射
    city_codes:
      "北京": "101010100"
      "上海": "101020100"
      "广州": "101280100"
      "深圳": "101280600"
      "杭州": "101210100"
      "成都": "101270100"
      "南京": "101190100"
      "武汉": "101200100"
      "西安": "101110100"
      "苏州": "101190400"
    # 经验代码映射
    experience_codes:
      "不限": "108"
      "1-3年": "101"
      "3-5年": "102"
      "5-10年": "103"
      "10年以上": "104"
  
  lagou:
    enabled: false
    name: "拉勾网"
    base_url: "https://www.lagou.com"
  
  liepin:
    enabled: false
    name: "猎聘"
    base_url: "https://www.liepin.com"

# 筛选规则
filter:
  # 大龄友好度阈值（0-100）
  min_score: 60
  
  # 正向信号（加分项）
  positive_signals:
    - "看重经验"
    - "资深"
    - "高级"
    - "架构"
    - "管理"
    - "不加班"
    - "弹性"
    - "扁平"
    - "技术驱动"
    - "15薪"
    - "16薪"
  
  # 负向信号（减分项）
  negative_signals:
    - "35岁以下"
    - "30岁以下"
    - "年轻团队"
    - "高强度"
    - "996"
    - "应届"
    - "实习"
    - "急聘"

# 简历优化系统对接
resume_optimizer:
  api_base: "http://localhost:8000/api/v1"

# 搜索历史
history:
  enabled: true
  file: "data/search_history.json"
  max_age_days: 30  # 历史记录保留天数
```

---

## 三、技术方案

### 3.1 平台适配模式

```python
# platforms/base.py
class BasePlatform(ABC):
    """招聘平台基类"""
    
    @abstractmethod
    async def search(self, keyword: str, city: str, experience: str) -> list[dict]:
        """搜索岗位"""
        pass
    
    @abstractmethod
    async def extract_jd(self, job_url: str) -> dict:
        """提取 JD 详情"""
        pass
    
    @abstractmethod
    def get_city_code(self, city_name: str) -> str:
        """获取城市代码"""
        pass

# platforms/boss.py
class BossPlatform(BasePlatform):
    """Boss直聘平台"""
    
    async def search(self, keyword, city, experience):
        city_code = self.get_city_code(city)
        exp_code = self.experience_codes.get(experience, "108")
        url = f"{self.search_url}?query={keyword}&city={city_code}&experience={exp_code}"
        # 打开页面、提取列表...
```

### 3.2 浏览器操作封装

```python
# browser.py
class BrowserController:
    """OpenClaw Browser 控制器"""
    
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        """连接 OpenClaw Browser"""
        # 通过 CDP 连接
        pass
    
    async def open_page(self, url: str) -> Page:
        """打开页面"""
        pass
    
    async def get_snapshot(self) -> str:
        """获取页面快照"""
        pass
    
    async def extract_elements(self, selector: str) -> list:
        """提取页面元素"""
        pass
    
    async def scroll_page(self):
        """滚动页面（模拟人工）"""
        pass
    
    async def wait_random(self, min_ms=1000, max_ms=3000):
        """随机等待（防反爬）"""
        pass
```

### 3.3 JD 分析器

```python
# analyzer.py
class JDAnalyzer:
    """JD 分析器 - 判断大龄友好度"""
    
    def __init__(self, config: dict):
        self.positive_signals = config.get("positive_signals", [])
        self.negative_signals = config.get("negative_signals", [])
    
    def analyze(self, jd_text: str) -> dict:
        """分析 JD"""
        positive_found = [s for s in self.positive_signals if s in jd_text]
        negative_found = [s for s in self.negative_signals if s in jd_text]
        
        # 计算分数
        score = 50  # 基础分
        score += len(positive_found) * 10
        score -= len(negative_found) * 15
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "friendly": score >= 60,
            "positive_signals": positive_found,
            "negative_signals": negative_found,
        }
```

### 3.4 系统导入器

```python
# importer.py
class SystemImporter:
    """导入简历优化系统"""
    
    def __init__(self, api_base: str):
        self.api_base = api_base
    
    async def import_job(self, job_data: dict) -> dict:
        """导入单个岗位"""
        # 1. 创建公司
        company = await self._create_company(job_data["company"])
        
        # 2. 创建 JD
        jd = await self._create_jd(company["id"], job_data)
        
        # 3. 自动解析 JD
        if self.auto_parse:
            await self._parse_jd(jd["id"])
        
        return {"company": company, "jd": jd}
    
    async def _create_company(self, company_data: dict) -> dict:
        """创建公司"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_base}/companies", json=company_data)
            return resp.json()
    
    async def _create_jd(self, company_id: str, job_data: dict) -> dict:
        """创建 JD"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_base}/jd", json={
                "company_id": company_id,
                "title": job_data["title"],
                "raw_text": job_data["description"],
                "source_url": job_data["url"],
            })
            return resp.json()
```

### 3.5 主入口

```python
# main.py
import argparse
from platforms.boss import BossPlatform
from analyzer import JDAnalyzer
from importer import SystemImporter

def main():
    parser = argparse.ArgumentParser(description="Job Hunter - 求职岗位自动筛选")
    subparsers = parser.add_subparsers(dest="command")
    
    # search 子命令
    search_parser = subparsers.add_parser("search", help="搜索岗位")
    search_parser.add_argument("-k", "--keyword", action="append", help="关键词")
    search_parser.add_argument("-c", "--city", default="上海", help="城市")
    search_parser.add_argument("-p", "--platform", default="boss", help="平台")
    search_parser.add_argument("-i", "--import", action="store_true", help="自动导入")
    search_parser.add_argument("-l", "--limit", type=int, default=20, help="最大数量")
    search_parser.add_argument("-s", "--min-score", type=int, default=60, help="最低分数")
    
    # import 子命令
    import_parser = subparsers.add_parser("import", help="导入岗位")
    import_parser.add_argument("-f", "--file", help="导入文件")
    
    args = parser.parse_args()
    
    if args.command == "search":
        asyncio.run(search_jobs(args))
    elif args.command == "import":
        asyncio.run(import_jobs(args))

async def search_jobs(args):
    # 加载配置
    config = load_config()
    
    # 初始化平台
    platform = get_platform(args.platform, config)
    
    # 初始化分析器
    analyzer = JDAnalyzer(config["filter"])
    
    # 搜索岗位
    keywords = args.keyword or config["search"]["keywords"]
    jobs = []
    for keyword in keywords:
        result = await platform.search(keyword, args.city, config["search"]["experience"])
        jobs.extend(result)
    
    # 分析筛选
    filtered = []
    for job in jobs:
        analysis = analyzer.analyze(job["description"])
        job["analysis"] = analysis
        if analysis["score"] >= args.min_score:
            filtered.append(job)
    
    # 输出结果
    print_results(filtered)
    
    # 导入系统
    if args.import:
        importer = SystemImporter(config["resume_optimizer"]["api_base"])
        for job in filtered:
            await importer.import_job(job)
```

---

## 四、核心流程

### 4.1 搜索流程

```
用户触发: python3 scripts/main.py search -k "技术经理" -c 上海
       │
       ▼
加载 config.yaml 配置
       │
       ▼
连接 OpenClaw Browser (CDP)
       │
       ▼
检查登录状态
  ├─ 已登录 → 继续
  └─ 未登录 → 提示用户登录，等待
       │
       ▼
构造搜索 URL
  https://www.zhipin.com/web/geek/job?query=技术经理&city=101020100&experience=103
       │
       ▼
打开搜索页面
       │
       ▼
提取职位列表 (循环翻页)
  ├─ 职位名称
  ├─ 公司名称
  ├─ 薪资范围
  ├─ 经验要求
  ├─ 公司规模
  └─ 详情链接
       │
       ▼
进入详情页提取完整 JD
       │
       ▼
分析大龄友好度 (正向/负向信号)
       │
       ▼
筛选符合条件的岗位 (score >= 60)
       │
       ▼
输出结果表格
       │
       ▼ (如指定 --import)
调用简历优化系统 API 导入
```

### 4.2 导入流程

```
搜索结果 (filtered jobs)
       │
       ▼
遍历每个岗位
       │
       ▼
调用 API: POST /companies
  { name, industry, size }
       │
       ▼
调用 API: POST /jd
  { company_id, title, raw_text, source_url }
       │
       ▼ (如 auto_parse=true)
调用 API: POST /jd/{id}/parse
       │
       ▼
返回导入结果
```

---

## 五、反爬策略

| 策略 | 实现方式 |
|------|----------|
| 请求频率控制 | 每次操作间隔 3-5 秒随机等待 |
| 模拟人工操作 | 随机滚动、移动鼠标 |
| 使用真实浏览器 | OpenClaw Browser（非无头模式） |
| 分批搜索 | 每次最多 20 个岗位 |
| 随机 User-Agent | 使用浏览器默认 UA |
| 避免频繁翻页 | 每次搜索最多 3 页 |

---

## 六、依赖说明

```bash
# Python 依赖
pip3 install playwright httpx pyyaml

# OpenClaw Browser
openclaw browser start --profile openclaw
```

---

## 七、开发计划

| 阶段 | 任务 | 工期 | 交付物 |
|------|------|------|--------|
| **Phase 1** | Skill 框架 + 配置管理 | 1天 | 基础结构 |
| **Phase 2** | 浏览器封装 + Boss直聘搜索 | 2天 | 搜索功能 |
| **Phase 3** | JD 提取 + 大龄友好分析 | 2天 | 智能筛选 |
| **Phase 4** | API 对接 + 批量导入 | 2天 | 系统集成 |
| **Phase 5** | 测试 + 优化 | 1天 | 稳定版本 |
| **合计** | | **8天** | **v1.0** |

---

## 八、后续扩展

| 扩展 | 说明 |
|------|------|
| 拉勾网支持 | Phase 2 |
| 猎聘支持 | Phase 2 |
| 智能推荐 | 基于简历自动推荐关键词 |
| 投递跟踪 | 记录投递状态 |
| 薪资分析 | 市场薪资水平分析 |
| 公司调研 | 自动收集公司信息 |
| 定时搜索 | Cron 定时执行搜索 |

---

*文档结束，等待确认后开始开发。*
