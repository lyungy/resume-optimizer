"""
Boss直聘平台适配器
模拟真人操作：首页搜索框输入 → 点击搜索 → 搜索页提取
"""
import asyncio
import random
import re
from typing import Optional
from .base import BasePlatform, JobInfo
from ..human import HumanSimulator


# 平台水印噪音模式
_NOISE_PATTERNS = [
    re.compile(r'来自BOSS直聘', re.IGNORECASE),
    re.compile(r'岗位[来自]*BOSS直聘', re.IGNORECASE),
    re.compile(r'BOSS直聘', re.IGNORECASE),
    re.compile(r'boss', re.IGNORECASE),
    re.compile(r'kanzhun', re.IGNORECASE),
    re.compile(r'直聘'),
]


def _clean_jd_text(text: str) -> str:
    """去除 Boss直聘平台水印噪音"""
    if not text:
        return text
    cleaned = text
    for pattern in _NOISE_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    return re.sub(r'  +', ' ', cleaned).strip()


# ========== 选择器常量 ==========

# 首页选择器
SEL_HOME_INPUT = "input.ipt-search"
SEL_HOME_BUTTON = "button.btn-search"
SEL_HOME_CITY_HIDDEN = "input.city-code"

# 搜索页选择器
SEL_SEARCH_INPUT = "div.search-input-box input.input"
SEL_SEARCH_INPUT_FALLBACK = 'input[placeholder*="搜索"]'
SEL_SEARCH_BUTTON = "a.search-btn"
SEL_CLEAR_BUTTON = "a.clear-search-btn"
SEL_CITY_LABEL = "div.city-label"

# 通用选择器
SEL_JOB_LIST = "ul.rec-job-list"
SEL_JOB_CARD = "li.job-card-box"
SEL_JOB_CARD_ALT = ".job-card-box, .job-list-box li"


class BossPlatform(BasePlatform):
    """Boss直聘平台"""

    def __init__(self, config: dict, browser):
        super().__init__(config)
        self.browser = browser
        self.detail_interval = config.get("detail_interval", [3, 6])
        self.human = HumanSimulator(browser.page, config.get("human", {}))
        self._is_on_search_page = False

    async def search(
        self,
        keyword: str,
        city: str,
        experience: str,
        limit: int = 20,
        fetch_detail: bool = False,
        is_first: bool = True,
    ) -> list[JobInfo]:
        """
        搜索岗位

        Args:
            keyword: 搜索关键词
            city: 城市名称
            experience: 经验要求
            limit: 最大返回数量
            fetch_detail: 是否抓取详情页
            is_first: 是否首个关键词（决定从首页搜还是搜索页内搜）
        """
        # 1. 进入搜索页
        if is_first or not self._is_on_search_page:
            await self._search_from_home(keyword, city)
        else:
            await self._search_from_search_page(keyword)

        self._is_on_search_page = True

        # 2. 等待职位列表加载
        loaded = await self._wait_for_job_list()
        if not loaded:
            print(f"  ⚠️ 页面加载超时，可能需要登录或被反爬拦截")
            return []

        # 3. 滚动加载（模拟真人滚动）
        target_count = min(limit, 45)
        await self._scroll_to_load(target_count)

        # 4. 提取职位列表
        jobs = await self._extract_jobs_from_page()
        jobs = jobs[:limit]
        print(f"  📊 列表提取: {len(jobs)} 个岗位")

        # 5. 可选：提取详情页 JD
        if fetch_detail and jobs:
            await self._fetch_details(jobs)

        return jobs

    # ========== 搜索流程 ==========

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
        try:
            await self.human.click(SEL_HOME_INPUT)
        except ValueError:
            # 兜底：尝试通用选择器
            await self.human.click(SEL_SEARCH_INPUT_FALLBACK)
        await self.human.random_pause(0.3, 0.8)

        # 逐字输入关键词
        try:
            await self.human.type_text(SEL_HOME_INPUT, keyword)
        except ValueError:
            await self.human.type_text(SEL_SEARCH_INPUT_FALLBACK, keyword)
        await self.human.random_pause(0.8, 1.5)

        # 点击搜索按钮
        try:
            await self.human.click(SEL_HOME_BUTTON)
        except ValueError:
            await self.human.click(SEL_SEARCH_BUTTON)

        # 等待页面跳转
        await self.human.wait_for_page_ready()
        await self.human.random_pause(1, 2)

    async def _search_from_search_page(self, keyword: str):
        """在搜索页内清空重输（后续关键词）"""
        print(f"  📍 搜索页切换: {keyword}")

        # 点击清空按钮（如果存在）
        try:
            clear_btn = await self.browser.query_selector(SEL_CLEAR_BUTTON)
            if clear_btn:
                await self.human.click(SEL_CLEAR_BUTTON)
                await self.human.random_pause(0.3, 0.5)
        except Exception:
            pass

        # 点击搜索框
        try:
            await self.human.click(SEL_SEARCH_INPUT)
        except ValueError:
            await self.human.click(SEL_SEARCH_INPUT_FALLBACK)
        await self.human.random_pause(0.2, 0.5)

        # 清空输入框
        try:
            await self.human.clear_input(SEL_SEARCH_INPUT)
        except ValueError:
            await self.human.clear_input(SEL_SEARCH_INPUT_FALLBACK)
        await self.human.random_pause(0.3, 0.5)

        # 验证清空，残留则重试
        for _attempt in range(2):
            current = ''
            for sel in [SEL_SEARCH_INPUT, SEL_SEARCH_INPUT_FALLBACK]:
                try:
                    current = await self.browser.evaluate(
                        f"() => document.querySelector('{sel}')?.value || ''"
                    )
                    if current:
                        break
                except Exception:
                    continue
            if not current:
                break
            # 重试：重新聚焦 + Ctrl+A + Delete
            print(f"  ⚠️ 搜索框残留 '{current}'，重试清空")
            try:
                await self.human.click(SEL_SEARCH_INPUT)
            except ValueError:
                await self.human.click(SEL_SEARCH_INPUT_FALLBACK)
            await self.browser.page.keyboard.press('Meta+a')
            await asyncio.sleep(0.1)
            await self.browser.page.keyboard.press('Delete')
            await self.human.random_pause(0.3, 0.5)

        # 逐字输入新关键词
        try:
            await self.human.type_text(SEL_SEARCH_INPUT, keyword)
        except ValueError:
            await self.human.type_text(SEL_SEARCH_INPUT_FALLBACK, keyword)
        await self.human.random_pause(0.8, 1.5)

        # 点击搜索按钮
        await self.human.click(SEL_SEARCH_BUTTON)

        # 等待页面加载
        await self.human.wait_for_page_ready()
        await self.human.random_pause(1, 2)

    async def _set_city_via_dom(self, city_code: str):
        """通过 DOM 设置城市代码"""
        await self.browser.evaluate(f"""
            () => {{
                const cityInput = document.querySelector('{SEL_HOME_CITY_HIDDEN}');
                if (cityInput) {{
                    cityInput.value = '{city_code}';
                    cityInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}
        """)

    # ========== 职位列表 ==========

    async def _wait_for_job_list(self) -> bool:
        """等待职位列表加载"""
        selectors = [SEL_JOB_LIST, SEL_JOB_CARD, SEL_JOB_CARD_ALT]
        for sel in selectors:
            if await self.browser.wait_for_selector(sel, timeout=15000):
                return True
        return False

    async def _scroll_to_load(self, target_count: int):
        """滚动加载更多职位（模拟真人滚动）"""
        prev_count = 0
        max_scrolls = 10
        no_change_count = 0

        for i in range(max_scrolls):
            current_count = await self.browser.evaluate(
                f'() => document.querySelectorAll("{SEL_JOB_CARD}").length'
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

            # 模拟真人滚动
            await self.human.scroll_page()

    async def _extract_jobs_from_page(self) -> list[JobInfo]:
        """从当前页提取职位列表"""
        js_code = """
        () => {
            const jobs = [];
            const cards = document.querySelectorAll('li.job-card-box');

            for (const card of cards) {
                try {
                    const titleLink = card.querySelector('a.job-name');
                    const title = titleLink?.textContent?.trim() || '';
                    let jobUrl = titleLink?.getAttribute('href') || '';
                    if (jobUrl && !jobUrl.startsWith('http')) {
                        jobUrl = 'https://www.zhipin.com' + jobUrl;
                    }

                    const salaryEl = card.querySelector('.job-salary');
                    const salary = salaryEl?.textContent?.trim() || '';

                    const tagEls = card.querySelectorAll('.tag-list li');
                    const tags = Array.from(tagEls).map(el => el.textContent?.trim()).filter(Boolean);

                    const companyEl = card.querySelector('.boss-name');
                    const companyName = companyEl?.textContent?.trim() || '';
                    const companyLinkEl = card.querySelector('.boss-info');
                    let companyUrl = companyLinkEl?.getAttribute('href') || '';
                    if (companyUrl && !companyUrl.startsWith('http') && companyUrl !== 'javascript:;') {
                        companyUrl = 'https://www.zhipin.com' + companyUrl;
                    }

                    const locationEl = card.querySelector('.company-location');
                    const location = locationEl?.textContent?.trim() || '';

                    if (title && companyName) {
                        jobs.push({
                            title,
                            company_name: companyName,
                            company_url: companyUrl.startsWith('http') ? companyUrl : '',
                            salary,
                            tags,
                            industry: '',
                            location,
                            url: jobUrl.startsWith('http') ? jobUrl : '',
                        });
                    }
                } catch(e) {
                    continue;
                }
            }
            return jobs;
        }
        """
        try:
            raw_jobs = await self.browser.evaluate(js_code)
        except Exception as e:
            print(f"  ⚠️ JS 提取失败: {e}")
            return []

        jobs = []
        for raw in raw_jobs:
            experience = raw["tags"][0] if len(raw["tags"]) > 0 else ""
            education = raw["tags"][1] if len(raw["tags"]) > 1 else ""
            company_size = raw["tags"][2] if len(raw["tags"]) > 2 else ""

            job = JobInfo(
                title=raw["title"],
                company_name=raw["company_name"],
                company_url=raw.get("company_url", ""),
                salary=raw["salary"],
                experience=experience,
                education=education,
                company_size=company_size,
                industry=raw.get("industry", ""),
                location=raw.get("location", ""),
                url=raw.get("url", ""),
                platform="boss",
                tags=raw.get("tags", []),
            )
            jobs.append(job)

        return jobs

    # ========== 详情页 ==========

    async def _fetch_details(self, jobs: list[JobInfo]):
        """批量提取详情页 JD（带频率控制）"""
        total = len(jobs)
        print(f"  📄 开始提取详情页 ({total} 个)...")

        for i, job in enumerate(jobs):
            if not job.url:
                continue

            print(f"    [{i+1}/{total}] {job.title} - {job.company_name}")
            jd_text = await self._extract_jd_detail(job.url)
            job.description = jd_text

            if i < total - 1:
                delay = random.uniform(*self.detail_interval)
                await asyncio.sleep(delay)

        print(f"  ✅ 详情页提取完成")

    async def extract_jd(self, job_url: str) -> str:
        """提取 JD 详情（公开接口）"""
        return await self._extract_jd_detail(job_url)

    async def _extract_jd_detail(self, job_url: str) -> str:
        """提取单个 JD 详情"""
        try:
            await self.browser.open_page(job_url)

            loaded = await self.browser.wait_for_selector(
                ".job-detail-section, .job-sec-text, .text",
                timeout=10000
            )
            if not loaded:
                return ""

            jd_text = await self.browser.evaluate("""
            () => {
                const descEl = document.querySelector('.job-detail-section .job-sec-text, .job-sec-text');
                const desc = descEl?.textContent?.trim() || '';

                const tagEls = document.querySelectorAll('.job-detail-tags .tag-icon, .job-label-list li');
                const tags = Array.from(tagEls).map(t => t.textContent?.trim()).filter(Boolean);

                return desc + (tags.length ? '\\n\\n标签: ' + tags.join(', ') : '');
            }
            """)

            return _clean_jd_text(jd_text or "")

        except Exception as e:
            print(f"    ⚠️ 提取详情失败: {e}")
            return ""
