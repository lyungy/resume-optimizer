"""
人机行为模拟器
模拟真人鼠标移动、键盘输入、滚动、点击等行为，降低反爬检测风险
"""
import asyncio
import random
from typing import Optional


class HumanSimulator:
    """人机行为模拟器"""

    def __init__(self, page, config: dict = None):
        self.page = page
        config = config or {}

        # 输入配置
        self.type_delay_min = config.get("type_delay_min", 80)
        self.type_delay_max = config.get("type_delay_max", 200)
        self.type_pause_chance = config.get("type_pause_chance", 0.15)
        self.type_pause_min = config.get("type_pause_min", 300)
        self.type_pause_max = config.get("type_pause_max", 800)
        self.typo_chance = config.get("typo_chance", 0.05)

        # 鼠标配置
        self.mouse_move_steps_min = config.get("mouse_move_steps_min", 10)
        self.mouse_move_steps_max = config.get("mouse_move_steps_max", 20)

        # 滚动配置
        self.scroll_distance_min = config.get("scroll_distance_min", 300)
        self.scroll_distance_max = config.get("scroll_distance_max", 600)

        # 鼠标当前位置跟踪
        self._mouse_x = 0.0
        self._mouse_y = 0.0

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
            # 元素可能被遮挡，尝试用 JS 点击
            await self.page.evaluate(f"""
                () => {{
                    const el = document.querySelector('{selector}');
                    if (el) el.click();
                }}
            """)
            return

        # 目标点：元素中心附近随机偏移
        target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

        # 鼠标移动
        await self.move_mouse_to(target_x, target_y)

        # 点击前短暂停顿
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # 点击
        await self.page.mouse.click(target_x, target_y)

    async def click_element(self, el):
        """
        模拟真人点击（直接传入元素对象）
        """
        box = await el.bounding_box()
        if not box:
            await el.click()
            return

        target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
        target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

        await self.move_mouse_to(target_x, target_y)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await self.page.mouse.click(target_x, target_y)

    async def move_mouse_to(self, x: float, y: float):
        """
        贝塞尔曲线鼠标移动
        模拟真人鼠标轨迹：先加速后减速，有微小抖动
        """
        start_x, start_y = self._mouse_x, self._mouse_y

        # 生成贝塞尔控制点（带随机偏移，模拟手部抖动）
        dist_x = x - start_x
        dist_y = y - start_y

        ctrl1 = {
            "x": start_x + dist_x * 0.3 + random.uniform(-20, 20),
            "y": start_y + dist_y * 0.1 + random.uniform(-15, 15),
        }
        ctrl2 = {
            "x": start_x + dist_x * 0.7 + random.uniform(-15, 15),
            "y": start_y + dist_y * 0.9 + random.uniform(-10, 10),
        }

        # 分步移动
        steps = random.randint(self.mouse_move_steps_min, self.mouse_move_steps_max)

        for i in range(steps + 1):
            t = i / steps
            # 三次贝塞尔公式
            mt = 1 - t
            px = (mt**3 * start_x + 3 * mt**2 * t * ctrl1["x"] +
                  3 * mt * t**2 * ctrl2["x"] + t**3 * x)
            py = (mt**3 * start_y + 3 * mt**2 * t * ctrl1["y"] +
                  3 * mt * t**2 * ctrl2["y"] + t**3 * y)

            await self.page.mouse.move(px, py)
            # 每步间隔：先快后慢（模拟减速）
            speed_factor = 1.0 + (t - 0.5) * 0.6  # 中间快，两端慢
            await asyncio.sleep(random.uniform(0.005, 0.02) * speed_factor)

        # 更新位置
        self._mouse_x = x
        self._mouse_y = y

    async def type_text(self, selector: str, text: str):
        """
        模拟真人逐字输入
        - 每个字符间隔 80-200ms
        - 15% 概率额外停顿 300-800ms（模拟思考）
        - 5% 概率输入错误后删除重打
        """
        el = await self.page.query_selector(selector)
        if not el:
            raise ValueError(f"输入框未找到: {selector}")

        await el.click()
        await asyncio.sleep(random.uniform(0.3, 0.6))

        for i, char in enumerate(text):
            # 概率打错字
            if random.random() < self.typo_chance and i < len(text) - 1:
                wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                await self.page.keyboard.type(wrong_char, delay=random.randint(50, 100))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))

            # 输入正确字符
            delay = random.randint(self.type_delay_min, self.type_delay_max)
            await self.page.keyboard.type(char, delay=delay)

            # 概率额外停顿
            if random.random() < self.type_pause_chance:
                pause = random.uniform(
                    self.type_pause_min / 1000,
                    self.type_pause_max / 1000
                )
                await asyncio.sleep(pause)

    async def clear_input(self, selector: str):
        """
        清空输入框（模拟真人操作）
        随机选择方式：双击全选+删除 / Ctrl+A+删除 / 连续Backspace
        """
        el = await self.page.query_selector(selector)
        if not el:
            raise ValueError(f"输入框未找到: {selector}")

        await el.click()
        await asyncio.sleep(random.uniform(0.2, 0.4))

        method = random.choice(["double_click", "ctrl_a", "backspace"])

        if method == "double_click":
            await el.dblclick()
            await asyncio.sleep(random.uniform(0.1, 0.2))
            await self.page.keyboard.press("Delete")
        elif method == "ctrl_a":
            await self.page.keyboard.press("Meta+a")
            await asyncio.sleep(random.uniform(0.1, 0.2))
            await self.page.keyboard.press("Delete")
        else:
            # 连续 Backspace
            text_len = await el.evaluate("el => el.value.length")
            for _ in range(text_len):
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.02, 0.06))

        await asyncio.sleep(random.uniform(0.2, 0.4))

    async def scroll_page(self, distance: int = None):
        """
        模拟真人滚动
        - 带惯性：先快后慢
        - 每次滚动距离随机
        - 滚动后随机停顿
        """
        if distance is None:
            distance = random.randint(self.scroll_distance_min, self.scroll_distance_max)

        # 分多步滚动（模拟手指滑动惯性）
        steps = random.randint(3, 6)
        remaining = distance

        for i in range(steps):
            # 逐步减速
            ratio = (steps - i) / steps
            step_distance = max(20, int(distance / steps * ratio * random.uniform(0.8, 1.2)))

            if step_distance > remaining:
                step_distance = remaining

            await self.page.evaluate(f"window.scrollBy(0, {step_distance})")
            remaining -= step_distance

            # 每步间隔（逐步变慢）
            await asyncio.sleep(random.uniform(0.05, 0.15) * (1 + i * 0.3))

        # 滚动后停顿
        await self.random_pause(0.5, 1.5)

    async def random_pause(self, min_s: float = 0.5, max_s: float = 2.0):
        """
        随机停顿（正态分布，更接近真人行为）
        """
        mean = (min_s + max_s) / 2
        std = (max_s - min_s) / 4
        delay = max(min_s, min(max_s, random.gauss(mean, std)))
        await asyncio.sleep(delay)

    async def wait_for_page_ready(self, timeout_ms: int = 10000):
        """等待页面加载完成"""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        except Exception:
            pass
