# Boss直聘 DOM 结构调研文档

> 版本：v1.0 | 日期：2026-05-24
> 工具：Patchright 反检测浏览器实测

---

## 一、页面体系概述

Boss直聘前端是 **SPA 架构**，首页和搜索页使用不同的模板引擎：

| 页面 | URL | 渲染方式 | 搜索框选择器 |
|------|-----|---------|-------------|
| **首页** | `zhipin.com` → 重定向到 `/shanghai/` | 传统 HTML 模板 | `input.ipt-search` (name=query) |
| **搜索页** | `/web/geek/job?query=xxx&city=xxx` | Vue SPA (data-v-* 属性) | `input.input` (无 name) |

**关键发现**：两套页面的 DOM 结构完全不同，不能用同一套选择器。

---

## 二、首页 DOM 结构

### 2.1 页面层次

```
body
├── div.standard.grayBody
│   └── div.home-body.home-body-wrapper
│       └── div.column-search-panel.search-panel-new
│           └── div.search-box.is-login
│               ├── div.search-form              ← 搜索表单容器
│               │   └── div.search-form-con      ← 搜索表单内容
│               │       ├── div.ipt-wrap          ← 输入框容器
│               │       │   └── input.ipt-search  ← 🔍 搜索输入框
│               │       │       name="query"
│               │       │       placeholder="搜索职位、公司"
│               │       ├── a.btn-map-search      ← 地图按钮
│               │       └── button.btn.btn-search ← 🔍 搜索按钮
│               │
│               ├── input.city-code [hidden]      ← 城市代码 (name=city)
│               ├── input.industry-code [hidden]  ← 行业代码
│               ├── input.position-code [hidden]  ← 职位代码
│               │
│               └── div.search-hot                ← 热门搜索词
│                   └── a[href] × N
```

### 2.2 搜索框交互

```python
# 首页搜索框
input_selector = "input.ipt-search"        # 或 input[name="query"]
button_selector = "button.btn.btn-search"  # 搜索按钮

# 隐藏字段（可读取/设置城市）
city_input = "input.city-code"             # name="city", value="101020100"
```

### 2.3 搜索表单提交机制

首页是传统表单，点击搜索按钮会构造 URL 跳转：
```
GET /web/geek/job?query={关键词}&city={城市代码}
```

隐藏字段 `input.city-code` 的 value 决定搜索城市。

---

## 三、搜索页 DOM 结构（Vue SPA）

### 3.1 页面层次

```
body
└── div.page-jobs.has-header.page-header-v2
    └── div.page-jobs-main
        ├── header / nav                    ← 顶部导航
        └── div.job-search-form             ← 🔍 搜索区域（Vue 组件）
            ├── svg.search-icon             ← 搜索图标
            ├── div.search-input-box        ← 输入框容器
            │   └── div.input-wrap.input-wrap-text
            │       └── input.input         ← 🔍 搜索输入框
            │           placeholder="搜索职位、公司"
            │           autocomplete="on"
            ├── a.search-btn                ← 🔍 搜索按钮 (text="搜索")
            ├── a.clear-search-btn          ← 清空按钮
            └── div.city-label.active       ← 城市选择器 (text="上海")

        ├── div.filter-condition            ← 筛选条件栏
        │   ├── div.city-area-select        ← 城市区域选择
        │   ├── [薪资待遇]
        │   ├── [工作经验]
        │   ├── [学历要求]
        │   ├── [公司行业]
        │   └── [公司规模]
        │
        └── div.job-list-container          ← 职位列表容器
            └── ul.rec-job-list             ← 职位列表（每页15个）
                └── div.job-card-wrap × N   ← 职位卡片
                    └── li.job-card-box
                        ├── img.job-tag-icon     ← 猎头等标签图标
                        ├── div.job-info
                        │   ├── div.job-title.clearfix
                        │   │   ├── a.job-name       ← 职位名称
                        │   │   └── span.job-salary   ← 薪资
                        │   └── ul.tag-list
                        │       ├── li              ← 经验要求
                        │       └── li              ← 学历要求
                        └── div.job-card-footer
                            ├── a.boss-info
                            │   ├── div.boss-logo   ← 公司 logo
                            │   └── div.boss-name   ← 公司名称
                            └── span.company-location ← 工作地点
```

### 3.2 搜索框交互

```python
# 搜索页搜索框
input_selector = "div.search-input-box input.input"
button_selector = "a.search-btn"

# 更通用（推荐）
input_selector = 'input[placeholder*="搜索"]'   # 首页和搜索页通用
button_selector = 'a.search-btn, button.btn-search'  # 两种按钮都匹配
```

### 3.3 城市选择器

```python
city_label = "div.city-label.active"     # 当前城市（可点击展开）
cur_city = "span.cur-city-label"         # 当前城市文字
city_dialog = ".city-select-dialog"      # 城市选择弹窗
city_area = ".city-area-dropdown"        # 区域下拉
```

---

## 四、职位卡片字段选择器

### 4.1 列表页字段

| 字段 | 选择器 | 示例值 |
|------|--------|--------|
| 职位名称 | `a.job-name` | 架构师/技术经理 |
| 薪资 | `span.job-salary` | 30-50K |
| 经验要求 | `ul.tag-list li:nth-child(1)` | 10年以上 |
| 学历要求 | `ul.tag-list li:nth-child(2)` | 本科 |
| 公司名称 | `div.boss-name` 或 `.company-name` | 某大型知名医疗健康上市公司 |
| 工作地点 | `span.company-location` | 上海 |
| 公司链接 | `a.boss-info[href]` | /gongsi/xxx.html |
| 职位链接 | `a.job-name[href]` | /job_detail/xxx.html |
| 标签图标 | `img.job-tag-icon` | 猎头 |

### 4.2 职位卡片完整结构

```python
# 提取单个职位信息的 JS 代码
extract_js = """
() => {
    const jobs = [];
    const cards = document.querySelectorAll('li.job-card-box');
    
    for (const card of cards) {
        try {
            const nameEl = card.querySelector('a.job-name');
            const salaryEl = card.querySelector('.job-salary');
            const tagEls = card.querySelectorAll('.tag-list li');
            const companyEl = card.querySelector('.boss-name');
            const locationEl = card.querySelector('.company-location');
            const logoEl = card.querySelector('.boss-logo img');
            
            let jobUrl = nameEl?.getAttribute('href') || '';
            if (jobUrl && !jobUrl.startsWith('http')) {
                jobUrl = 'https://www.zhipin.com' + jobUrl;
            }
            
            jobs.push({
                title: nameEl?.textContent?.trim() || '',
                url: jobUrl,
                salary: salaryEl?.textContent?.trim() || '',
                experience: tagEls[0]?.textContent?.trim() || '',
                education: tagEls[1]?.textContent?.trim() || '',
                company_name: companyEl?.textContent?.trim() || '',
                location: locationEl?.textContent?.trim() || '',
                tags: Array.from(tagEls).map(t => t.textContent?.trim()),
            });
        } catch(e) {
            continue;
        }
    }
    return jobs;
}
"""
```

---

## 五、当前方案问题分析

### 5.1 现有搜索方式

```python
# 当前代码（boss.py 第 59-62 行）
url = f"{self.search_url}?{urllib.parse.urlencode(params)}"
await self.browser.open_page(url)
```

直接构造 URL 访问，存在以下问题：

| 问题 | 影响 | 严重度 |
|------|------|--------|
| **无 Referer** | 直接访问搜索 URL，没有从首页跳转的 referer 头 | 🔴 高 |
| **无鼠标/键盘操作** | 没有点击搜索框、输入文字、点击按钮的过程 | 🔴 高 |
| **URL 参数规律明显** | 固定格式 `?query=xxx&city=xxx` | 🟡 中 |
| **访问频率固定** | 间隔时间太规律 | 🟡 中 |
| **无首页停留** | 跳过首页直接访问搜索页 | 🟡 中 |

### 5.2 反爬检测维度

Boss直聘的反爬检测主要在以下层面：

```
┌─────────────────────────────────────────────┐
│ 1. 浏览器指纹                               │
│    - navigator.webdriver → Patchright 已绕过 │
│    - Canvas/WebGL 指纹                       │
├─────────────────────────────────────────────┤
│ 2. 行为分析                                  │
│    - 鼠标移动轨迹                            │
│    - 键盘输入速度/间隔                        │
│    - 页面停留时间                            │
│    - 滚动行为                                │
├─────────────────────────────────────────────┤
│ 3. 请求特征                                  │
│    - Referer 来源                            │
│    - URL 直接访问 vs 页面内跳转               │
│    - 请求频率                                │
├─────────────────────────────────────────────┤
│ 4. 环境检测                                  │
│    - console.table 计时检测 CDP              │
│    - 插件/扩展检测                            │
│    - DNS 解析行为                            │
└─────────────────────────────────────────────┘
```

---

## 六、优化方案：模拟人操作搜索

### 6.1 核心思路

```
当前：直接构造 URL 访问搜索结果
  → 容易被识别为爬虫

优化：从首页进入 → 点击搜索框 → 逐字输入关键词 → 点击搜索按钮
  → 模拟真实用户行为，携带正确 Referer
```

### 6.2 详细流程

```
Step 1: 打开首页
    │  URL: https://www.zhipin.com
    │  等待 2-4s（页面加载 + 随机延迟）
    │
    ▼
Step 2: 设置城市（可选）
    │  方式A: 修改隐藏字段 input.city-code 的 value
    │  方式B: 点击城市选择器 → 选择目标城市
    │  等待 1-2s
    │
    ▼
Step 3: 点击搜索框
    │  选择器: input.ipt-search (首页)
    │  模拟鼠标移动到搜索框 → 点击
    │  等待 0.5-1s
    │
    ▼
Step 4: 逐字输入关键词
    │  模拟键盘输入，每个字符间隔 80-200ms（随机）
    │  例如: "架" → 等120ms → "构" → 等150ms → "师"
    │  输入完成后等待 1-2s
    │
    ▼
Step 5: 点击搜索按钮
    │  选择器: button.btn-search (首页)
    │  等待页面跳转（自动变成搜索页 URL）
    │  Referer 自动携带为首页 URL ✅
    │
    ▼
Step 6: 等待搜索结果加载
    │  等待选择器: ul.rec-job-list 或 li.job-card-box
    │  超时: 10s
    │
    ▼
Step 7: 正常滚动 + 提取数据
    │  （沿用现有逻辑）
    ▼
```

### 6.3 实现要点

#### 6.3.1 人机输入模拟

```python
async def human_type(page, selector: str, text: str):
    """模拟人类逐字输入"""
    el = await page.query_selector(selector)
    await el.click()
    await asyncio.sleep(random.uniform(0.3, 0.8))
    
    for char in text:
        await page.keyboard.type(char, delay=random.randint(80, 200))
        # 偶尔停顿更久（模拟思考）
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.3, 0.8))
```

#### 6.3.2 鼠标移动模拟

```python
async def human_click(page, selector: str):
    """模拟人类鼠标移动 + 点击"""
    el = await page.query_selector(selector)
    box = await el.bounding_box()
    
    # 目标点（元素中心附近随机偏移）
    x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
    y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
    
    # 移动鼠标（分多步，模拟真人轨迹）
    await page.mouse.move(x, y, steps=random.randint(5, 15))
    await asyncio.sleep(random.uniform(0.1, 0.3))
    await page.mouse.click(x, y)
```

#### 6.3.3 城市设置

```python
async def set_city(page, city_code: str):
    """通过隐藏字段设置城市"""
    await page.evaluate(f"""
        () => {{
            const cityInput = document.querySelector('input.city-code');
            if (cityInput) cityInput.value = '{city_code}';
        }}
    """)
```

### 6.4 两种进入搜索页的方式

| 方式 | 流程 | 优点 | 缺点 |
|------|------|------|------|
| **A. 首页搜索** | 首页 → 输入 → 点击搜索 → 跳转搜索页 | Referer 正确，行为自然 | 需要处理首页和搜索页两套 DOM |
| **B. 搜索页内搜索** | 直接进搜索页 → 清空输入框 → 重新输入 → 点击搜索 | 只需一套 DOM | 首次访问仍无 referer |

**推荐方案 A**，完整模拟用户从首页开始的搜索行为。

### 6.5 多关键词搜索优化

当搜索多个关键词时，不应每次都从首页开始：

```
首页搜索第一个关键词 → 搜索页
    │
    ├─ 清空搜索框（点击 clear-search-btn）
    ├─ 输入第二个关键词
    ├─ 点击搜索
    │
    ├─ 清空搜索框
    ├─ 输入第三个关键词
    ├─ 点击搜索
    │
    └─ ...（后续关键词在搜索页内完成）
```

---

## 七、等待选择器清单

| 用途 | 选择器 | 超时 |
|------|--------|------|
| 首页搜索框就绪 | `input.ipt-search` | 10s |
| 首页搜索按钮 | `button.btn-search` | 5s |
| 搜索页搜索框 | `input[placeholder*="搜索"]` | 10s |
| 搜索页搜索按钮 | `a.search-btn` | 5s |
| 城市选择器 | `div.city-label` | 5s |
| 职位列表加载 | `ul.rec-job-list` | 15s |
| 职位卡片出现 | `li.job-card-box` | 10s |
| 清空按钮 | `a.clear-search-btn` | 3s |

---

## 八、后续优化方向

### 8.1 短期（本次迭代）

- [x] DOM 结构分析
- [ ] 实现首页 → 搜索框 → 输入 → 搜索的完整流程
- [ ] 人机输入模拟（逐字输入、随机间隔）
- [ ] 鼠标移动模拟（贝塞尔曲线轨迹）
- [ ] 多关键词复用搜索页（清空重输）

### 8.2 中期

- [ ] 搜索下拉建议交互（输入后等待建议出现再回车）
- [ ] 筛选条件点击（薪资、经验、学历等下拉选择）
- [ ] 页面停留时间随机化（每页 3-8s）
- [ ] 滚动行为优化（模拟真人滚动速度和停顿）

### 8.3 长期

- [ ] 搜索词变体（同义词替换，降低重复模式）
- [ ] 访问时间分布（避免固定时间段）
- [ ] Cookie/Session 轮换策略
- [ ] 代理 IP 池集成

---

## 附录 A：完整选择器速查表

```python
SELECTORS = {
    # ========== 首页 ==========
    "home": {
        "search_input": "input.ipt-search",           # name="query"
        "search_input_by_name": 'input[name="query"]',
        "search_button": "button.btn-search",
        "city_hidden": "input.city-code",              # hidden, name="city"
        "form_container": "div.search-form-con",
    },
    
    # ========== 搜索页 ==========
    "search": {
        "search_input": 'div.search-input-box input.input',
        "search_input_generic": 'input[placeholder*="搜索"]',
        "search_button": "a.search-btn",
        "clear_button": "a.clear-search-btn",
        "city_label": "div.city-label.active",
        "city_dialog": ".city-select-dialog",
    },
    
    # ========== 通用（首页+搜索页都可用） ==========
    "common": {
        "search_input": 'input[placeholder*="搜索"]',
        "search_button": "a.search-btn, button.btn-search",
    },
    
    # ========== 职位列表 ==========
    "job_list": {
        "container": "ul.rec-job-list",
        "card": "li.job-card-box",
        "card_wrap": "div.job-card-wrap",
        "job_name": "a.job-name",
        "salary": ".job-salary",
        "tags": ".tag-list li",
        "company_name": ".boss-name",
        "location": ".company-location",
        "boss_info": "a.boss-info",
        "job_link": "a.job-name[href]",
    },
    
    # ========== 筛选条件 ==========
    "filter": {
        "container": "div.filter-condition",
        "city_area": ".city-area-select",
        "salary": "[class*='salary']",
        "experience": "[class*='experience']",
        "education": "[class*='education']",
    },
}
```

## 附录 B：首页搜索表单隐藏字段

| name | class | 说明 | 示例值 |
|------|-------|------|--------|
| `query` | `ipt-search` | 搜索关键词（可见） | 架构师 |
| `city` | `city-code` | 城市代码（hidden） | 101020100 |
| `industry` | `industry-code` | 行业代码（hidden） | - |
| `position` | `position-code` | 职位代码（hidden） | - |

---

*文档持续更新，后续优化迭代追加到第八节。*
