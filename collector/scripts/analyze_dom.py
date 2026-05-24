#!/usr/bin/env python3
"""
Boss直聘 DOM 结构分析脚本
使用 Patchright 反检测浏览器访问，输出页面关键元素的选择器和交互方式
"""
import asyncio
import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.browser import BrowserController


async def analyze_dom():
    """分析 Boss直聘页面 DOM 结构"""
    browser = BrowserController({
        "mode": "patchright",
        "headless": False,
        "timeout": 30,
        "min_interval": 1,
        "max_interval": 2,
    })

    connected = await browser.connect()
    if not connected:
        print("❌ 浏览器启动失败")
        return

    try:
        # ========== 1. 首页 ==========
        print("\n" + "=" * 60)
        print("📄 1. 首页 (zhipin.com)")
        print("=" * 60)

        await browser.open_page("https://www.zhipin.com")
        await asyncio.sleep(3)

        homepage = await browser.evaluate("""
        () => {
            const result = { url: location.href, title: document.title };
            
            // 搜索框
            const inputs = Array.from(document.querySelectorAll('input'));
            result.inputs = inputs.map(el => ({
                tag: el.tagName,
                id: el.id,
                name: el.name,
                type: el.type,
                placeholder: el.placeholder,
                className: el.className,
                parentClass: el.parentElement?.className,
                grandParentClass: el.parentElement?.parentElement?.className,
                visible: el.offsetParent !== null,
            }));
            
            // 按钮/链接
            const btns = Array.from(document.querySelectorAll('button, a.btn, a[class*="search"], a[class*="btn"], [class*="search-btn"]'));
            result.buttons = btns.slice(0, 15).map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.textContent?.trim()?.substring(0, 30),
                href: el.getAttribute('href'),
                cursor: el.offsetParent !== null,
            }));
            
            // 搜索区域容器
            const containers = Array.from(document.querySelectorAll('[class*="search"], [class*="Search"], [id*="search"]'));
            result.containers = containers.slice(0, 10).map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className,
                childCount: el.children.length,
                text: el.textContent?.trim()?.substring(0, 50),
            }));
            
            return result;
        }
        """)
        print(json.dumps(homepage, ensure_ascii=False, indent=2))

        # ========== 2. 搜索页 ==========
        print("\n" + "=" * 60)
        print("📄 2. 搜索页 (带参数 URL)")
        print("=" * 60)

        await browser.open_page("https://www.zhipin.com/web/geek/job?query=架构师&city=101020100")
        await asyncio.sleep(4)

        search_page = await browser.evaluate("""
        () => {
            const result = { url: location.href, title: document.title };
            
            // 搜索框区域
            const searchArea = document.querySelector('[class*="search-form"], [class*="search-box"], [class*="search-condition"], .search-condition-wrapper, .search-box-wrapper');
            if (searchArea) {
                result.searchArea = {
                    tag: searchArea.tagName,
                    className: searchArea.className,
                    innerHTML: searchArea.innerHTML.substring(0, 500),
                };
            }
            
            // 所有 input
            const inputs = Array.from(document.querySelectorAll('input'));
            result.inputs = inputs.map(el => ({
                id: el.id,
                name: el.name,
                type: el.type,
                placeholder: el.placeholder,
                className: el.className,
                parentClass: el.parentElement?.className,
                value: el.value,
                visible: el.offsetParent !== null,
            }));
            
            // 搜索按钮
            const searchBtns = Array.from(document.querySelectorAll('[class*="btn-search"], [class*="search-btn"], button[type="submit"]'));
            result.searchButtons = searchBtns.map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.textContent?.trim(),
            }));
            
            // 城市选择器
            const cityEls = Array.from(document.querySelectorAll('[class*="city"], [class*="City"]'));
            result.cityElements = cityEls.slice(0, 5).map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.textContent?.trim()?.substring(0, 30),
            }));
            
            // 筛选栏
            const filterEls = Array.from(document.querySelectorAll('[class*="filter"], [class*="condition"], [class*="dropdown"]'));
            result.filterElements = filterEls.slice(0, 10).map(el => ({
                tag: el.tagName,
                className: el.className,
                text: el.textContent?.trim()?.substring(0, 40),
            }));
            
            return result;
        }
        """)
        print(json.dumps(search_page, ensure_ascii=False, indent=2))

        # ========== 3. 职位列表 ==========
        print("\n" + "=" * 60)
        print("📄 3. 职位列表 DOM")
        print("=" * 60)

        job_list = await browser.evaluate("""
        () => {
            const result = {};
            
            // 职位卡片
            const cards = document.querySelectorAll('li.job-card-box, .job-card-wrapper, [class*="job-card"]');
            result.cardCount = cards.length;
            
            if (cards.length > 0) {
                const firstCard = cards[0];
                result.firstCard = {
                    tag: firstCard.tagName,
                    className: firstCard.className,
                    innerHTML: firstCard.innerHTML.substring(0, 800),
                };
                
                // 提取字段选择器
                result.fields = {
                    jobName: firstCard.querySelector('.job-name, [class*="job-name"]')?.textContent?.trim(),
                    jobNameSelector: firstCard.querySelector('.job-name, [class*="job-name"]')?.className,
                    salary: firstCard.querySelector('.salary, [class*="salary"]')?.textContent?.trim(),
                    salarySelector: firstCard.querySelector('.salary, [class*="salary"]')?.className,
                    companyName: firstCard.querySelector('.company-name, [class*="company-name"], h3, .boss-name')?.textContent?.trim(),
                    companySelector: firstCard.querySelector('.company-name, [class*="company-name"], h3, .boss-name')?.className,
                    location: firstCard.querySelector('[class*="area"], [class*="location"]')?.textContent?.trim(),
                    locationSelector: firstCard.querySelector('[class*="area"], [class*="location"]')?.className,
                    tags: Array.from(firstCard.querySelectorAll('.tag-list li, [class*="tag"] li')).map(t => t.textContent?.trim()),
                };
            }
            
            // 列表容器
            const listContainers = document.querySelectorAll('ul.job-list-box, .job-list-box, [class*="job-list"]');
            result.listContainers = Array.from(listContainers).map(el => ({
                tag: el.tagName,
                className: el.className,
                childCount: el.children.length,
            }));
            
            return result;
        }
        """)
        print(json.dumps(job_list, ensure_ascii=False, indent=2))

        # ========== 4. 搜索框交互分析 ==========
        print("\n" + "=" * 60)
        print("📄 4. 搜索框交互分析")
        print("=" * 60)

        interaction = await browser.evaluate("""
        () => {
            const result = {};
            
            // 找到搜索输入框（多种方式）
            const selectors = [
                'input[placeholder*="搜索"]',
                'input[placeholder*="职位"]',
                'input.ipt-search',
                '.search-input input',
                '.ipt-wrap input',
                'input[name="query"]',
                'input[type="text"]',
            ];
            
            result.inputSelectors = {};
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                result.inputSelectors[sel] = el ? {
                    found: true,
                    placeholder: el.placeholder,
                    className: el.className,
                    id: el.id,
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect(),
                } : { found: false };
            }
            
            // 找到搜索按钮
            const btnSelectors = [
                '.btn-search',
                'a.btn-search',
                'button.btn-search',
                '[class*="btn-search"]',
                '[class*="search-btn"]',
                'button[type="submit"]',
            ];
            
            result.buttonSelectors = {};
            for (const sel of btnSelectors) {
                const el = document.querySelector(sel);
                result.buttonSelectors[sel] = el ? {
                    found: true,
                    tag: el.tagName,
                    className: el.className,
                    text: el.textContent?.trim(),
                    rect: el.getBoundingClientRect(),
                } : { found: false };
            }
            
            // 城市选择器
            const citySelectors = [
                '.city-label',
                '.search-condition-wrapper .city',
                '[class*="city-label"]',
                '[class*="city-select"]',
            ];
            
            result.citySelectors = {};
            for (const sel of citySelectors) {
                const el = document.querySelector(sel);
                result.citySelectors[sel] = el ? {
                    found: true,
                    text: el.textContent?.trim(),
                    className: el.className,
                } : { found: false };
            }
            
            // 页面整体结构
            const mainContainer = document.querySelector('.page-container, .main-container, #wrap, .wrap');
            result.mainContainer = mainContainer ? {
                className: mainContainer.className,
                childClasses: Array.from(mainContainer.children).slice(0, 10).map(c => c.className),
            } : null;
            
            return result;
        }
        """)
        print(json.dumps(interaction, ensure_ascii=False, indent=2))

        # ========== 5. 搜索下拉建议 ==========
        print("\n" + "=" * 60)
        print("📄 5. 搜索下拉建议 (输入后)")
        print("=" * 60)

        # 尝试在搜索框输入文字
        input_found = await browser.evaluate("""
        () => {
            const input = document.querySelector('input[placeholder*="搜索"]') || 
                          document.querySelector('input[placeholder*="职位"]') ||
                          document.querySelector('.search-input input');
            if (input) {
                input.focus();
                input.value = '架构师';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                return { found: true, value: input.value };
            }
            return { found: false };
        }
        """)

        if input_found.get("found"):
            await asyncio.sleep(2)
            suggestions = await browser.evaluate("""
            () => {
                // 搜索下拉建议
                const dropdowns = document.querySelectorAll('[class*="suggest"], [class*="dropdown"], [class*="autocomplete"], [class*="search-result"]');
                return {
                    dropdownCount: dropdowns.length,
                    dropdowns: Array.from(dropdowns).slice(0, 5).map(d => ({
                        className: d.className,
                        visible: d.offsetParent !== null,
                        text: d.textContent?.trim()?.substring(0, 100),
                        childCount: d.children.length,
                    })),
                };
            }
            """)
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
        else:
            print("未找到搜索框，跳过下拉建议分析")

        # ========== 6. 页面完整 HTML 结构摘要 ==========
        print("\n" + "=" * 60)
        print("📄 6. 页面 body 主要结构")
        print("=" * 60)

        body_structure = await browser.evaluate("""
        () => {
            const body = document.body;
            function getStructure(el, depth = 0) {
                if (depth > 3) return null;
                const children = Array.from(el.children).slice(0, 8);
                return {
                    tag: el.tagName,
                    className: el.className?.substring(0, 80),
                    id: el.id,
                    childCount: el.children.length,
                    children: children.map(c => getStructure(c, depth + 1)).filter(Boolean),
                };
            }
            return getStructure(body);
        }
        """)
        print(json.dumps(body_structure, ensure_ascii=False, indent=2))

        print("\n✅ 分析完成")

    finally:
        await browser.disconnect()


if __name__ == "__main__":
    asyncio.run(analyze_dom())
