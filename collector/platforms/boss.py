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


def _clean_jd_text(text: str) -> str:
    """深度净化 Boss直聘 JD 文本"""
    if not text:
        return text

    # 1. 移除所有 CSS 代码块
    cleaned = re.sub(r'\.[A-Za-z_][\w-]*\s*\{[^}]*\}', '', text)
    cleaned = re.sub(r'[A-Za-z_][\w-]*\s*\{[^}]{5,}\}', '', cleaned)

    # 2. 移除残留的 CSS 属性值
    cleaned = re.sub(
        r'(?:display|visibility|overflow|font-style|font-weight|width|height)\s*:[^;{]+;?',
        '', cleaned
    )
    cleaned = re.sub(r'!important', '', cleaned)

    # 3. 提取 JD 核心段落（从职位描述/工作内容 到 关于我们/工作地址 之前）
    jd_start = None
    jd_end = None
    for marker in ['职位描述', '工作内容', '岗位职责', '岗位描述', '职责描述', '工作职责']:
        idx = cleaned.find(marker)
        if idx != -1:
            jd_start = idx + len(marker)
            break
    for marker in ['关于我们', '工作地址', '公司介绍', '公司信息']:
        idx = cleaned.find(marker)
        if idx != -1:
            jd_end = idx
            break
    if jd_start is not None:
        cleaned = cleaned[jd_start:]
    if jd_end is not None:
        cleaned = cleaned[:jd_end]

    # 4. 按行清理
    lines = cleaned.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过纯英文 CSS 残留
        if re.match(r'^[A-Za-z_.\s:{};-]+$', line):
            continue
        # 跳过 Boss 导航/广告关键词
        if any(kw in line for kw in [
            '热门职位', '热门城市', '热门企业', '附近城市', '求职工具',
            '升级VIP', '尊享特权', '去升级', '下载APP', '前往App',
            '去App', '微信扫码分享', '点击查看地图', '查看更多信息',
            '供应链经理招聘', '会务/会展策划', '4S店店长', '药店店员',
        ]):
            continue
        result.append(line)

    cleaned = '\n'.join(result)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


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
        # 采集数量范围
        result_range = config.get("result_range", {})
        self._result_min = result_range.get("min", 20)
        self._result_max = result_range.get("max", 40)

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

        # 3. 滚动加载（模拟真人滚动，随机目标数量）
        import random as _random
        scroll_target = _random.randint(self._result_min, self._result_max)
        print(f"  🎯 目标采集: {scroll_target} 条（配置范围: {self._result_min}~{self._result_max}）")
        await self._scroll_to_load(scroll_target)

        # 4. 提取职位列表（用随机目标数截断，不用 limit）
        jobs = await self._extract_jobs_from_page()
        jobs = jobs[:scroll_target]
        print(f"  📊 最终返回: {len(jobs)} 个岗位（目标 {scroll_target}）")

        # 5. 逐条点击列表，采集右栏详情
        if jobs:
            import logging
            _log = logging.getLogger(__name__)
            _log.warning(f">> 即将进入详情采集，jobs={len(jobs)}")
            try:
                await self._fetch_details_from_list(jobs)
                _log.warning(">> 详情采集调用完成")
            except Exception as e:
                _log.error(f">> 详情采集异常: {e}", exc_info=True)

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
        """滚动加载更多职位（模拟真人滚动，触发 lazy load）"""
        import random as _random

        prev_count = 0
        max_scrolls = 25
        no_change_count = 0
        max_no_change = 4  # 连续 N 次无新内容才放弃

        for i in range(max_scrolls):
            current_count = await self.browser.evaluate(
                f'() => document.querySelectorAll("{SEL_JOB_CARD}, {SEL_JOB_CARD_ALT}").length'
            )
            print(f"    滚动 {i+1}/{max_scrolls}: 当前 {current_count} 条，目标 {target_count} 条")

            if current_count >= target_count:
                break

            if current_count == prev_count:
                no_change_count += 1
                if no_change_count >= max_no_change:
                    print(f"    连续 {max_no_change} 次无新内容，停止滚动")
                    break
                # 无新内容时多等一下（lazy load 可能有延迟）
                await self.human.random_pause(1.0, 2.0)
            else:
                no_change_count = 0

            prev_count = current_count

            # 滚动到页面底部（触发 lazy load）
            await self.browser.evaluate(
                '() => window.scrollTo(0, document.documentElement.scrollHeight)'
            )

            # 模拟真人停顿：滚动后等一下看新内容
            await self.human.random_pause(0.8, 1.5)

            # 偶尔回滚一点（模拟真人浏览行为）
            if _random.random() < 0.3:
                back_dist = _random.randint(100, 300)
                await self.browser.evaluate(f'() => window.scrollBy(0, -{back_dist})')
                await self.human.random_pause(0.3, 0.8)

        final_count = await self.browser.evaluate(
            f'() => document.querySelectorAll("{SEL_JOB_CARD}, {SEL_JOB_CARD_ALT}").length'
        )
        print(f"    ✅ 滚动完成: {final_count} 条")

    async def _extract_jobs_from_page(self) -> list[JobInfo]:
        """从当前页提取职位列表"""
        js_code = """
        () => {
            const jobs = [];
            // 多选择器兼容
            const cards = document.querySelectorAll('li.job-card-box, .job-card-box, .job-list-box li');
            const totalCards = cards.length;
            let skipped = 0;

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
                    } else {
                        skipped++;
                    }
                } catch(e) {
                    skipped++;
                }
            }
            return {jobs, totalCards, skipped};
        }
        """
        try:
            result = await self.browser.evaluate(js_code)
            raw_jobs = result["jobs"]
            print(f"  🔍 DOM 卡片: {result['totalCards']} 个, 有效: {len(raw_jobs)} 个, 跳过: {result['skipped']} 个")
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

    # ========== 列表内点击详情 ==========

    # 右栏详情选择器
    SEL_DETAIL_TEXT = '.job-detail-section .job-sec-text, .job-sec-text, .job-detail .text'
    SEL_LEFT_CARDS = 'li.job-card-box, .job-card-box, .job-list-box li'

    async def _fetch_details_from_list(self, jobs: list[JobInfo]):
        """在搜索结果页逐条点击左栏卡片，采集右栏详情"""
        import random as _random
        import logging
        _log = logging.getLogger(__name__)

        total = len(jobs)
        max_details = 15
        click_rate = 0.65
        detail_count = 0
        clicked_urls = set()

        _log.warning(f">> 详情采集开始（最多 {max_details} 条）")

        # 先滚回顶部
        await self.browser.evaluate('() => window.scrollTo(0, 0)')
        await asyncio.sleep(1.5)

        # 循环：全部用 page.evaluate 操作 DOM（Patchright ElementHandle.evaluate 不兼容）
        no_new_count = 0
        sel_js = self.SEL_LEFT_CARDS.replace("'", "\\'")
        while detail_count < max_details:
            # 获取所有卡片 URL + index
            card_infos = await self.browser.evaluate(
                """() => { """
                f"const cards = document.querySelectorAll('{sel_js}');"
                """const r = [];
                cards.forEach((el, i) => {
                    const a = el.querySelector('a');
                    if (a && a.href) r.push({index: i, url: a.href});
                });
                return r; }"""
            )
            if not card_infos:
                break

            # 找一个没点过的卡片
            found = False
            for info in card_infos:
                if detail_count >= max_details:
                    break

                card_url = info.get('url', '')
                card_index = info.get('index', 0)
                if not card_url or card_url in clicked_urls:
                    continue

                if _random.random() > click_rate:
                    continue

                # 匹配 job
                matched_job = None
                for job in jobs:
                    if job.url == card_url:
                        matched_job = job
                        break
                if not matched_job:
                    continue

                try:
                    # JS: 滚动到卡片 + 点击
                    click_js = (
                        """() => { """
                        f"const cards = document.querySelectorAll('{sel_js}');"
                        f"const card = cards[{card_index}];"
                        """if (!card) return false;
                        card.scrollIntoView({behavior: 'instant', block: 'center'});
                        const link = card.querySelector('a');
                        if (link) link.addEventListener('click', e => e.preventDefault(), {once: true});
                        card.click();
                        return true; }"""
                    )
                    clicked = await self.browser.evaluate(click_js)
                    if not clicked:
                        continue

                    clicked_urls.add(card_url)
                    detail_count += 1
                    no_new_count = 0
                    _log.warning(f"    [{detail_count}] 点击: {matched_job.title}")

                    # 等待右栏渲染（Boss 加载可能较慢）
                    await asyncio.sleep(_random.uniform(2.0, 3.5))

                    # 提取「职位描述」下的内容
                    _M = '["\u804c\u4f4d\u63cf\u8ff0","\u5c97\u4f4d\u63cf\u8ff0","\u5c97\u4f4d\u804c\u8d23"]'
                    _S = '["\u4efb\u804c\u8981\u6c42","\u5c97\u4f4d\u8981\u6c42","\u5173\u4e8e\u6211\u4eec","\u516c\u53f8\u4ecb\u7ecd","\u798f\u5229\u5f85\u9047","\u5de5\u4f5c\u5730\u5740"]'
                    detail_text = await self.browser.evaluate(
                        "() => {"
                        "var MARKERS = " + _M + ";"
                        "var STOPS = " + _S + ";"
                        "var all = document.querySelectorAll('*');"
                        "var title = null;"
                        "for (var i = 0; i < all.length; i++) {"
                        "  var t = (all[i].textContent || '').trim();"
                        "  for (var j = 0; j < MARKERS.length; j++) {"
                        "    if (t === MARKERS[j]) { title = all[i]; break; }"
                        "  }"
                        "  if (title) break;"
                        "}"
                        "if (title) {"
                        "  var p = title.parentElement;"
                        "  while (p && p.children.length < 2 && p !== document.body) p = p.parentElement;"
                        "  if (p) {"
                        "    var on = false, parts = [];"
                        "    for (var k = 0; k < p.children.length; k++) {"
                        "      var c = p.children[k];"
                        "      if (c === title || c.contains(title)) { on = true; continue; }"
                        "      if (on) {"
                        "        var ct = (c.textContent || '').trim();"
                        "        var stop = false;"
                        "        for (var m = 0; m < STOPS.length; m++) {"
                        "          if (ct.indexOf(STOPS[m]) === 0 && ct.length < 20) { stop = true; break; }"
                        "        }"
                        "        if (stop) break;"
                        "        parts.push(ct);"
                        "      }"
                        "    }"
                        "    if (parts.length > 0) return {text: parts.join('\\n'), method: 'title'};"
                        "  }"
                        "}"
                        "var sels = ['.job-detail-section .job-sec-text', '.job-sec-text', '.job-detail-section', '.job-detail'];"
                        "for (var n = 0; n < sels.length; n++) {"
                        "  var e = document.querySelector(sels[n]);"
                        "  if (e && e.textContent.trim().length > 50) return {text: e.textContent.trim(), method: 'sel:' + sels[n]};"
                        "}"
                        "return {text: '', method: 'none'};"
                        "}"
                    )

                    if detail_text and detail_text.get('text'):
                        await self._simulate_reading()
                        matched_job.description = _clean_jd_text(detail_text['text'])
                        method = detail_text.get('method', '')
                        _log.warning(f"    [{detail_count}] ✅ {matched_job.title} ({len(matched_job.description)} 字) [{method}]")
                    else:
                        method = detail_text.get('method', '未知') if detail_text else 'null'
                        debug = detail_text.get('debug', []) if detail_text else []
                        debug_str = ''
                        if debug:
                            debug_str = '\n      '.join([
                                f"  {d.get('tag','?')}.{d.get('cls','')[:40]} id={d.get('id','')} text={d.get('text','')[:60]}..."
                                for d in debug[:5]
                            ])
                        _log.warning(f"    [{detail_count}] ⚠️ 详情为空: {matched_job.title} [{method}]")
                        if debug_str:
                            _log.warning(f"      右栏结构:\n      {debug_str}")

                    await self.human.random_pause(2.0, 4.0)

                    if detail_count > 0 and detail_count % _random.randint(5, 8) == 0:
                        rest = _random.uniform(6.0, 10.0)
                        _log.warning(f"    💤 休息 {rest:.0f}s...")
                        await asyncio.sleep(rest)

                    found = True
                    break  # 重新获取卡片列表

                except Exception as e:
                    _log.warning(f"    ⚠️ 失败: {matched_job.title} - {e}")
                    continue

            if not found:
                no_new_count += 1
                if no_new_count >= 3:
                    break
                await self.browser.evaluate('() => window.scrollBy(0, 300)')
                await asyncio.sleep(1.0)

        _log.warning(f">> 详情采集完成: {detail_count}/{total} 条")

    async def _simulate_reading(self):
        """模拟阅读右栏详情"""
        import random as _random
        scroll_rounds = _random.randint(1, 3)
        for _ in range(scroll_rounds):
            distance = _random.randint(100, 300)
            await self.browser.evaluate(
                f'() => {{ '
                f'const el = document.querySelector(".job-detail-section, .job-detail, .detail-content"); '
                f'if (el) el.scrollTop += {distance}; '
                f'else window.scrollBy(0, {distance}); }}'
            )
            await asyncio.sleep(_random.uniform(0.3, 1.0))

    # ========== 详情页（旧版，保留备用） ==========

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
