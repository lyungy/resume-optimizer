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
| `search` | 搜索岗位（支持多关键词、城市、详情页抓取） |
| `import` | 从上次搜索结果导入系统 |
| `history` | 查看搜索历史 |
| `clear-history` | 清空搜索历史 |
| `open-browser` | 打开浏览器（手动登录/操作） |
| `clean-jd` | 清洗数据库 JD 文本（去除平台水印） |

## 导入模式

在 `config.yaml` 中配置 `import.import_mode`：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `direct` | 直接调用 backend service | 项目内运行（默认） |
| `http` | 通过 REST API 调用 | 独立运行、解耦 |

## 配置

编辑 `config.yaml` 修改搜索条件、筛选规则、浏览器配置等。

## 首次使用

1. 安装依赖：`.venv/bin/pip install patchright`
2. 关闭所有 Chrome 浏览器
3. 运行 `.venv/bin/python -m collector open-browser` 打开浏览器
4. 在浏览器中手动登录 Boss直聘
5. 登录后关闭浏览器，后续搜索会自动复用登录态
