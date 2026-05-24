# Boss直聘反爬优化 - 技术设计方案

> 版本：v1.0 | 日期：2026-05-24
> 基于 DOM 结构调研文档（docs/BOSS_DOM_ANALYSIS.md）

---

## 一、问题分析

### 1.1 当前搜索流程

```
__main__.py 循环 keywords
    │
    └─► platform.search(keyword, city, ...)
            │
            ├─ 构造 URL: /web/geek/job?query=架构师&city=101020100
            ├─ browser.open_page(url)        ← 直接 goto，无 Referer
            ├─ 等待 ul.rec-job-list          ← 无鼠标/键盘操作
            ├─ scrollTo 底部循环加载          ← 滚动太机械
            └─ JS 提取职位卡片
```

**问题**：

| # | 问题 | 影响 |
|---|------|------|
| 1 | 直接 `goto(搜索URL)` | 无 Referer，服务端知道你不是从页面跳转来的 |
| 2 | 无搜索框交互 | 没有 focus → input → click 的行为链，与真人不符 |
| 3 | 多关键词每次都 `goto` | 每次都是新的直接访问，行为模式异常 |
| 4 | `scrollTo` 机械滚动 | 匀速瞬移到底部，无鼠标轨迹 |
| 5 | 操作间隔太规律 | `random.uniform(1.5, 2.5)` 分布太均匀 |

### 1.2 Boss直聘反爬检测维度

```
┌────────────────────────────────────────────────────────────┐
│ 请求层                                                     │
│   Referer 缺失 ✗ | URL 直接访问 ✗ | 频率规律 ✗             │
├────────────────────────────────────────────────────────────┤
│ 行为层                                                     │
│   无鼠标移动 ✗ | 无键盘输入 ✗ | 滚动机械 ✗ | 无页面停留 ✗  │
├────────────────────────────────────────────────────────────┤
│ 环境层                                                     │
│   Patchright 绕过 webdriver 检测 ✓ | 持久化登录态 ✓        │
└────────────────────────────────────────────────────────────┘
```

环境层已通过 Patchright 解决，**本次优化重点在请求层和行为层**。

---

## 二、优化目标

| 目标 | 具体指标 |
|------|----------|
| 搜索行为模拟 | 从首页进入，通过搜索框输入+点击完成搜索 |
| Referer 携带 | 搜索页请求 Referer 为首页 URL |
| 人机输入模拟 | 逐字输入，80-200ms 随机间隔，偶有停顿 |
| 鼠标轨迹模拟 | 贝塞尔曲线移动，非直线瞬移 |
| 多关键词优化 | 第一个关键词从首页搜，后续在搜索页清空重搜 |
| 操作间隔随机化 | 基于正态分布，非均匀分布 |
| 向后兼容 | 不改变现有接口签名，search() 入参不变 |

---

## 三、架构设计

### 3.1 模块划分

```
collector/
├── platforms/
│   ├── base.py              # 不变
│   └── boss.py              # 🔧 重构 search() 流程
├── browser.py               # 🔧 新增人机交互方法
├── human.py                 # 🆕 人机行为模拟器（独立模块）
├── analyzer.py              # 不变
├── importer.py              # 不变
├── config.yaml              # 🔧 新增 human 模拟配置
└── __main__.py              # 🔧 搜索循环改为传入 is_first 标记
```

### 3.2 新增模块：`human.py` — 人机行为模拟器

职责：封装所有人机交互行为，供 BossPlatform 调用。

```python
class HumanSimulator:
    """人机行为模拟器"""
    
    def __init__(self, page, config: dict):
        self.page = page
        self.config = config
    
    async def click(self, selector: str):
        """模拟真人点击（鼠标移动 + 点击）"""
        ...
    
    async def type_text(self, selector: str, text: str):
        """模拟真人逐字输入"""
        ...
    
    async def clear_input(self, selector: str):
        """清空输入框（全选+删除，模拟真人）"""
        ...
    
    async def scroll_page(self, direction: str = "down", distance: int = None):
        """模拟真人滚动（带惯性、停顿）"""
        ...
    
    async def move_mouse_to(self, x: int, y: int):
        """贝塞尔曲线鼠标移动"""
        ...
    
    async def random_pause(self, min_s: float = 0.5, max_s: float = 2.0):
        """随机停顿（正态分布）"""
        ...
```

### 3.3 核心流程变更

#### 变更前（当前）

```
search(keyword, city, ...) {
    url = build_url(keyword, city)
    await browser.open_page(url)           # 直接 goto
    await wait_for_job_list()
    await scroll_to_load()
    return extract_jobs()
}
```

#### 变更后

```
search(keyword, city, ..., is_first=True) {
    if is_first:
        # 首个关键词：从首页搜索
        await self._search_from_home(keyword, city)
    else:
        # 后续关键词：在搜索页清空重输
        await self._search_from_search_page(keyword)
    
    await wait_for_job_list()
    await scroll_to_load()
    return extract_jobs()
}

_search_from_home(keyword, city) {
    await browser.open_page("https://www.zhipin.com")
    await human.random_pause(2, 4)
    
    # 设置城市（修改隐藏字段）
    await self._set_city(city)
    await human.random_pause(0.5, 1)
    
    # 点击搜索框
    await human.click("input.ipt-search")
    await human.random_pause(0.3, 0.8)
    
    # 逐字输入关键词
    await human.type_text("input.ipt-search", keyword)
    await human.random_pause(0.8, 1.5)
    
    # 点击搜索按钮
    await human.click("button.btn-search")
    
    # 等待搜索页加载（URL 会自动变成 /web/geek/jobs?query=...）
    await wait_for_job_list()
}

_search_from_search_page(keyword) {
    # 点击清空按钮
    await human.click("a.clear-search-btn")
    await human.random_pause(0.3, 0.5)
    
    # 点击搜索框
    await human.click("div.search-input-box input.input")
    await human.random_pause(0.2, 0.5)
    
    # 逐字输入新关键词
    await human.type_text("div.search-input-box input.input", keyword)
    await human.random_pause(0.8, 1.5)
    
    # 点击搜索按钮
    await human.click("a.search-btn")
    await wait_for_job_list()
}
```

---

## 四、详细设计

### 4.1 `human.py` — 人机行为模拟器

#### 4.1.1 鼠标移动（贝塞尔曲线）

```python
async def move_mouse_to(self, x: int, y: int):
    """
    贝塞尔曲线鼠标移动
    模拟真人鼠标轨迹：先加速后减速，有微小抖动
    """
    # 当前鼠标位置
    current = await self.page.evaluate("() => ({ x: 0, y: 0 })")  # 需要跟踪
    
    # 生成贝塞尔控制点（2个控制点的三次贝塞尔）
    ctrl1 = {
        "x": current["x"] + (x - current["x"]) * 0.3 + random.randint(-20, 20),
        "y": current["y"] + (y - current["y"]) * 0.1 + random.randint(-15, 15),
    }
    ctrl2 = {
        "x": current["x"] + (x - current["x"]) * 0.7 + random.randint(-15, 15),
        "y": current["y"] + (y - current["y"]) * 0.9 + random.randint(-10, 10),
    }
    
    # 分步移动（10-20步）
    steps = random.randint(10, 20)
    for i in range(steps + 1):
        t = i / steps
        # 三次贝塞尔公式
        px = (1-t)**3 * current["x"] + 3*(1-t)**2*t * ctrl1["x"] + \
             3*(1-t)*t**2 * ctrl2["x"] + t**3 * x
        py = (1-t)**3 * current["y"] + 3*(1-t)**2*t * ctrl1["y"] + \
             3*(1-t)*t**2 * ctrl2["y"] + t**3 * y
        
        await self.page.mouse.move(px, py)
        await asyncio.sleep(random.uniform(0.005, 0.02))  # 每步 5-20ms
```

#### 4.1.2 逐字输入

```python
async def type_text(self, selector: str, text: str):
    """
    模拟真人逐字输入
    - 每个字符间隔 80-200ms
    - 15% 概率额外停顿 300-800ms（模拟思考）
    - 5% 概率输入错误后删除重打
    """
    el = await self.page.query_selector(selector)
    await el.click()
    await asyncio.sleep(random.uniform(0.3, 0.6))
    
    for i, char in enumerate(text):
        # 5% 概率打错字
        if random.random() < 0.05 and i < len(text) - 1:
            wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
            await self.page.keyboard.type(wrong_char, delay=random.randint(50, 100))
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # 输入正确字符
        await self.page.keyboard.type(char, delay=random.randint(80, 200))
        
        # 15% 概率额外停顿
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.3, 0.8))
```

#### 4.1.3 真人点击

```python
async def click(self, selector: str):
    """
    模拟真人点击
    1. 找到元素
    2. 鼠标贝塞尔曲线移动到元素附近（中心偏移）
    3. 短暂停顿
    4. 点击
    """
    el = await self.page.query_selector(selector)
    if not el:
        raise ValueError(f"元素未找到: {selector}")
    
    box = await el.bounding_box()
    if not box:
        raise ValueError(f"元素不可见: {selector}")
    
    # 目标点：元素中心附近随机偏移
    target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
    target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)
    
    # 鼠标移动
    await self.move_mouse_to(target_x, target_y)
    
    # 点击前短暂停顿
    await asyncio.sleep(random.uniform(0.05, 0.15))
    
    # 点击
    await self.page.mouse.click(target_x, target_y)
```

#### 4.1.4 清空输入框

```python
async def clear_input(self, selector: str):
    """
    清空输入框（模拟真人操作）
    方式1: 双击全选 + Delete
    方式2: Ctrl+A + Delete
    方式3: 连续 Backspace
    随机选择一种
    """
    el = await self.page.query_selector(selector)
    await el.click()
    await asyncio.sleep(random.uniform(0.2, 0.4))
    
    method = random.choice(["double_click", "ctrl_a", "backspace"])
    
    if method == "double_click":
        await el.dblclick()
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await self.page.keyboard.press("Delete")
    elif method == "ctrl_a":
        await self.page.keyboard.press("Meta+a")  # macOS
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await self.page.keyboard.press("Delete")
    else:
        # 连续 Backspace
        text_len = await el.evaluate("el => el.value.length")
        for _ in range(text_len):
            await self.page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.02, 0.06))
    
    await asyncio.sleep(random.uniform(0.2, 0.4))
```

#### 4.1.5 模拟滚动

```python
async def scroll_page(self, distance: int = None):
    """
    模拟真人滚动
    - 带惯性：先快后慢
    - 每次滚动距离随机
    - 滚动后随机停顿
    """
    if distance is None:
        distance = random.randint(300, 600)
    
    # 分多步滚动（模拟手指滑动惯性）
    steps = random.randint(3, 6)
    for i in range(steps):
        step_distance = distance // steps
        # 逐步减速
        if i > steps // 2:
            step_distance = int(step_distance * 0.6)
        
        await self.page.evaluate(f"window.scrollBy(0, {step_distance})")
        await asyncio.sleep(random.uniform(0.05, 0.15))
    
    # 滚动后停顿
    await self.random_pause(0.5, 1.5)
```

#### 4.1.6 随机停顿

```python
async def random_pause(self, min_s: float = 0.5, max_s: float = 2.0):
    """
    随机停顿（正态分布，更接近真人）
    """
    mean = (min_s + max_s) / 2
    std = (max_s - min_s) / 4
    delay = max(min_s, min(max_s, random.gauss(mean, std)))
    await asyncio.sleep(delay)
```

---

### 4.2 `boss.py` — 搜索流程重构

#### 4.2.1 类变更

```python
class BossPlatform(BasePlatform):
    def __init__(self, config: dict, browser):
        super().__init__(config)
        self.browser = browser
        self.human = HumanSimulator(browser.page, config.get("human", {}))
        self._is_on_search_page = False  # 是否已在搜索页
```

#### 4.2.2 search() 方法变更

```python
async def search(
    self,
    keyword: str,
    city: str,
    experience: str,
    limit: int = 20,
    fetch_detail: bool = False,
    is_first: bool = True,           # 🆕 是否首个关键词
) -> list[JobInfo]:
    """搜索岗位"""
    
    # 1. 进入搜索页（两种路径）
    if is_first or not self._is_on_search_page:
        await self._search_from_home(keyword, city)
    else:
        await self._search_from_search_page(keyword)
    
    self._is_on_search_page = True
    
    # 2. 等待职位列表
    loaded = await self._wait_for_job_list()
    if not loaded:
        print(f"  ⚠️ 页面加载超时")
        return []
    
    # 3. 滚动加载（改用真人滚动）
    target_count = min(limit, 45)
    await self._scroll_to_load(target_count)
    
    # 4. 提取职位
    jobs = await self._extract_jobs_from_page()
    jobs = jobs[:limit]
    print(f"  📊 列表提取: {len(jobs)} 个岗位")
    
    # 5. 详情页（可选）
    if fetch_detail and jobs:
        await self._fetch_details(jobs)
    
    return jobs
```

#### 4.2.3 新增方法

```python
async def _search_from_home(self, keyword: str, city: str):
    """从首页通过搜索框搜索（首个关键词）"""
    print(f"  📍 首页搜索: {keyword} | {city}")
    
    # 打开首页
    await self.browser.open_page("https://www.zhipin.com")
    await self.human.random_pause(2, 4)
    
    # 设置城市
    city_code = self.get_city_code(city)
    if city_code:
        await self._set_city_via_dom(city_code)
        await self.human.random_pause(0.5, 1)
    
    # 点击搜索框
    await self.human.click("input.ipt-search")
    await self.human.random_pause(0.3, 0.8)
    
    # 逐字输入关键词
    await self.human.type_text("input.ipt-search", keyword)
    await self.human.random_pause(0.8, 1.5)
    
    # 点击搜索按钮
    await self.human.click("button.btn-search")
    
    # 等待页面跳转
    await self.human.random_pause(1, 2)


async def _search_from_search_page(self, keyword: str):
    """在搜索页内清空重输（后续关键词）"""
    print(f"  📍 搜索页切换: {keyword}")
    
    # 清空搜索框
    await self.human.clear_input("div.search-input-box input.input")
    await self.human.random_pause(0.3, 0.5)
    
    # 逐字输入新关键词
    await self.human.type_text("div.search-input-box input.input", keyword)
    await self.human.random_pause(0.8, 1.5)
    
    # 点击搜索按钮
    await self.human.click("a.search-btn")
    await self.human.random_pause(1, 2)


async def _set_city_via_dom(self, city_code: str):
    """通过 DOM 设置城市代码"""
    await self.browser.evaluate(f"""
        () => {{
            const cityInput = document.querySelector('input.city-code');
            if (cityInput) {{
                cityInput.value = '{city_code}';
                cityInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }}
    """)
```

#### 4.2.4 滚动加载改造

```python
async def _scroll_to_load(self, target_count: int):
    """滚动加载更多职位（模拟真人）"""
    prev_count = 0
    max_scrolls = 10
    no_change_count = 0

    for i in range(max_scrolls):
        current_count = await self.browser.evaluate(
            '() => document.querySelectorAll("li.job-card-box").length'
        )
        if current_count >= target_count:
            break
        if current_count == prev_count:
            no_change_count += 1
            if no_change_count >= 2:
                break
        else:
            no_change_count = 0
        prev_count = current_count

        # 🆕 改用真人滚动
        await self.human.scroll_page()
```

---

### 4.3 `__main__.py` — 搜索循环改造

```python
# 变更前：
for keyword in keywords:
    jobs = await platform.search(keyword, city, ...)

# 变更后：
for i, keyword in enumerate(keywords):
    print(f"\n🔎 搜索: {keyword}")
    jobs = await platform.search(
        keyword, city, ...,
        is_first=(i == 0),  # 🆕 标记是否首个关键词
    )
```

---

### 4.4 `browser.py` — 小幅调整

`open_page` 方法保持不变，新增 `page` 属性暴露给 `HumanSimulator`：

```python
# HumanSimulator 需要直接访问 page 对象来做 mouse.move / keyboard.type
# 当前 browser.py 已有 self.page，HumanSimulator 通过构造函数传入
```

无需改动 `browser.py`。

---

### 4.5 `config.yaml` — 新增 human 配置

```yaml
# ============================================================
# 人机行为模拟配置
# ============================================================
human:
  # 逐字输入间隔（ms）
  type_delay_min: 80
  type_delay_max: 200
  # 输入额外停顿概率
  type_pause_chance: 0.15
  type_pause_min: 300
  type_pause_max: 800
  # 打错字概率
  typo_chance: 0.05
  # 鼠标移动步数
  mouse_move_steps_min: 10
  mouse_move_steps_max: 20
  # 搜索间隔（秒，首页搜索后到搜索页搜索的间隔）
  search_interval_min: 3
  search_interval_max: 6
  # 滚动距离（像素）
  scroll_distance_min: 300
  scroll_distance_max: 600
```

---

## 五、变更影响分析

### 5.1 接口兼容性

| 接口 | 变更 | 兼容性 |
|------|------|--------|
| `BossPlatform.search()` | 新增 `is_first` 参数（默认 `True`） | ✅ 向后兼容 |
| `BrowserController` | 不变 | ✅ 无影响 |
| `HumanSimulator` | 🆕 新增模块 | ✅ 无影响 |
| `__main__.py` | 搜索循环传入 `is_first` | ✅ 功能不变 |
| `config.yaml` | 新增 `human` 配置段 | ✅ 有默认值 |

### 5.2 文件变更清单

| 文件 | 操作 | 变更量 |
|------|------|--------|
| `collector/human.py` | 🆕 新增 | ~180 行 |
| `collector/platforms/boss.py` | 🔧 重构 | ~80 行改动 |
| `collector/__main__.py` | 🔧 小改 | ~5 行 |
| `collector/config.yaml` | 🔧 新增配置 | ~15 行 |
| `docs/BOSS_DOM_ANALYSIS.md` | 已完成 | - |
| `docs/BOSS_ANTI_BAN_DESIGN.md` | 🆕 本文档 | - |

### 5.3 风险评估

| 风险 | 等级 | 应对 |
|------|------|------|
| 搜索框选择器变更 | 中 | DOM 分析脚本可定期验证，选择器已用多种兜底 |
| 城市设置不生效 | 低 | hidden 字段方案 + 点击城市选择器兜底 |
| 输入法兼容 | 低 | Patchright 环境固定，keyboard.type 逐字符输入 |
| 性能下降 | 低 | 人机模拟增加约 5-10s / 搜索，可接受 |

---

## 六、开发计划

| 阶段 | 任务 | 预计工时 |
|------|------|----------|
| 1 | 实现 `human.py`（人机行为模拟器） | 2h |
| 2 | 重构 `boss.py` 搜索流程（首页→搜索框→搜索） | 1.5h |
| 3 | 改造 `__main__.py` 搜索循环 | 0.5h |
| 4 | 新增 `config.yaml` human 配置 | 0.5h |
| 5 | 联调测试（多关键词、多城市） | 1h |
| **合计** | | **5.5h** |

---

## 七、验证方案

### 7.1 单元验证

```bash
# 验证人机输入模拟
python -c "
import asyncio
from collector.human import HumanSimulator
# 单独测试输入模拟
"

# 验证搜索流程
python -m collector search -k "架构师" -c 上海 -l 5
```

### 7.2 验证点

| 验证项 | 预期结果 |
|--------|----------|
| 首页搜索框输入 | 逐字输入，页面跳转到搜索结果页 |
| Referer 携带 | 搜索页请求的 Referer 包含首页 URL |
| 多关键词切换 | 第二个关键词在搜索页内清空重输 |
| 职位提取 | 提取数量与直接 URL 方式一致 |
| 连续运行 | 10 次搜索无反爬拦截 |

---

*文档结束，等待确认后开始开发。*
