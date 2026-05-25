# Collector - 求职岗位自动采集模块

从招聘平台自动搜索岗位，智能筛选对大龄友好的公司，导入简历优化系统。

## 快速开始

```bash
cd /Users/agent/Workspace/resume-optimizer

# 激活虚拟环境
source .venv/bin/activate

# 搜索岗位
python -m collector search -k "架构师" -c 上海

# 搜索并自动导入
python -m collector search -k "架构师" -c 上海 --import

# 从上次搜索结果导入
python -m collector import

# 打开浏览器（手动登录）
python -m collector open-browser
```

## CLI 命令

| 命令 | 说明 |
|------|------|
| `search` | 搜索岗位（支持多关键词、城市、详情采集） |
| `import` | 从上次搜索结果导入系统 |
| `history` | 查看搜索历史 |
| `clear-history` | 清空搜索历史 |
| `open-browser` | 打开浏览器（手动登录/操作） |
| `clean-jd` | 清洗数据库 JD 文本（去除平台噪音） |

## 配置说明

编辑 `config.yaml`：

```yaml
boss:
  # 采集数量范围（每次随机取区间内值）
  result_range:
    min: 20
    max: 40

  # 城市代码
  city_codes:
    上海: 101020100

  # 经验筛选
  experience_codes:
    "不限": 109900

  # 仿真操作参数
  human:
    click_detail_rate: 0.65   # 点击详情概率
    scroll_speed: [0.3, 0.8]  # 滚动速度范围
    typing_delay: [50, 150]   # 打字延迟范围

# 导入模式
import:
  import_mode: direct  # direct | http
```

## 采集流程

```
1. 首页搜索框输入关键词 → 点击搜索
         ↓
2. 搜索结果页滚动加载（目标 20~40 条）
         ↓
3. DOM 提取职位卡片信息（标题/公司/地点/薪资/URL）
         ↓
4. 列表页点击卡片 → 采集右栏详情（JD 正文）
         ↓
5. JD 文本净化（CSS 去噪、段落提取）
         ↓
6. 大龄友好度分析
         ↓
7. 去重 + 批量导入系统
```

## 关键技术点

### 反爬策略

- **贝塞尔曲线鼠标移动**：模拟真人鼠标轨迹
- **逐字输入**：搜索框模拟真人打字，非 Playwright fill
- **随机延迟**：操作间随机等待，避免固定节奏
- **滚动加载**：随机滚动目标，40% 概率回滚，容忍度机制
- **详情采集概率**：65% 概率点击详情，非全部采集

### 列表页详情采集

在搜索结果页直接点击左栏卡片，读取右栏详情面板，无需跳转详情页：

- 用 `page.evaluate()` 操作 DOM（兼容 Patchright）
- 滚动回顶部 → 重新获取卡片 → 逐个点击
- 最多采集 15 条详情，中途随机休息

### JD 文本净化

采集到的原始文本包含大量噪音，净化流程：

1. 移除 CSS 代码块（`.XXX{display:none!important;}`）
2. 移除残留 CSS 属性（display/visibility/font-style 等）
3. 提取「职位描述」到「关于我们」之间的核心段落
4. 行级过滤：跳过 Boss 导航/广告/UI 元素

## 导入模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `direct` | 直接调用 backend service | 项目内运行（默认） |
| `http` | 通过 REST API 调用 | 独立运行、解耦 |

## 首次使用

1. 安装依赖：`.venv/bin/pip install patchright`
2. 关闭所有 Chrome 浏览器
3. 运行 `.venv/bin/python -m collector open-browser` 打开浏览器
4. 在浏览器中手动登录 Boss直聘
5. 登录后关闭浏览器，后续搜索会自动复用登录态
