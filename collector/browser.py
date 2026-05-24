"""
浏览器控制器
支持两种模式：
  1. patchright（默认）：独立启动反检测浏览器
  2. cdp：连接已有浏览器（会被 Boss直聘检测）
"""
from __future__ import annotations
import asyncio
import signal
import subprocess
import random
from pathlib import Path
from typing import Any, Optional

# 数据目录（浏览器 profile、搜索结果等）
DATA_DIR = Path(__file__).resolve().parent / "data"


class BrowserController:
    """浏览器控制器"""

    def __init__(self, config: dict):
        self.mode = config.get("mode", "patchright")
        self.cdp_url = config.get("cdp_url", "http://localhost:18800")
        self.timeout = config.get("timeout", 30) * 1000
        self.min_interval = config.get("min_interval", 1)
        self.max_interval = config.get("max_interval", 2)
        self.max_scrolls = config.get("max_scrolls", 5)
        self.headless = config.get("headless", False)

        self.playwright: Any = None
        self.browser: Any = None
        self.context: Any = None
        self.page: Any = None
        self._profile_path: Optional[str] = None

    async def connect(self) -> bool:
        """连接或启动浏览器"""
        if self.mode == "cdp":
            return await self._connect_cdp()
        else:
            return await self._connect_patchright()

    async def _connect_patchright(self) -> bool:
        """用 Patchright 启动独立浏览器（反检测，持久化登录态）"""
        try:
            from patchright.async_api import async_playwright
        except ImportError:
            print("❌ patchright 未安装，请运行: pip install patchright")
            return False

        try:
            self._profile_path = str(DATA_DIR / "browser-profile")
            Path(self._profile_path).mkdir(parents=True, exist_ok=True)

            self.playwright = await async_playwright().start()

            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self._profile_path,
                headless=self.headless,
                viewport={"width": 1440, "height": 900},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--no-proxy-server",
                    "--no-sandbox",
                ],
                ignore_default_args=["--enable-automation"],
            )
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

            print(f"  ✅ Patchright 浏览器已启动")
            return True

        except Exception as e:
            print(f"❌ Patchright 启动失败: {e}")
            return False

    async def _connect_cdp(self) -> bool:
        """通过 CDP 连接已有浏览器"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ playwright 未安装")
            return False
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            return True
        except Exception as e:
            print(f"❌ CDP 连接失败: {e}")
            return False

    async def disconnect(self):
        """优雅关闭浏览器（带超时保护，不触发 Chrome 恢复机制）"""
        # 1. 关闭所有页面
        if self.context:
            try:
                for page in self.context.pages:
                    try:
                        await asyncio.wait_for(page.close(), timeout=3)
                    except Exception:
                        pass
            except Exception:
                pass

        # 2. 关闭 context（带超时保护）
        if self.context:
            try:
                await asyncio.wait_for(self.context.close(), timeout=8)
            except asyncio.TimeoutError:
                print("  ⚠️ context.close() 超时，尝试 SIGTERM 清理")
                self._sigterm_cleanup()
            except Exception:
                pass

        # 3. 停止 playwright（带超时保护）
        if self.playwright:
            try:
                await asyncio.wait_for(self.playwright.stop(), timeout=5)
            except asyncio.TimeoutError:
                print("  ⚠️ playwright.stop() 超时，跳过")
            except Exception:
                pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def _sigterm_cleanup(self):
        """SIGTERM 优雅清理残留进程（不用 SIGKILL）"""
        if not self._profile_path:
            return
        try:
            result = subprocess.run(
                ["pgrep", "-f", "browser-profile"],
                capture_output=True, text=True, timeout=3
            )
            for pid in result.stdout.strip().split('\n'):
                if pid and pid.isdigit():
                    try:
                        import os
                        os.kill(int(pid), signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        pass
        except Exception:
            pass

    def cleanup_stale_processes(self):
        """清理残留的 Patchright Chrome 进程（用 SIGTERM，不用 SIGKILL）"""
        if not self._profile_path:
            return
        try:
            result = subprocess.run(
                ["pgrep", "-f", "browser-profile"],
                capture_output=True, text=True, timeout=3
            )
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid and pid.isdigit():
                    try:
                        import os
                        os.kill(int(pid), signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        pass
        except Exception:
            pass

    async def open_page(self, url: str, retries: int = 3):
        """打开页面（带 DNS 重试）"""
        if not self.page:
            raise RuntimeError("浏览器未连接")
        for attempt in range(retries):
            try:
                await self.page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                await self._human_delay()
                return self.page
            except Exception as e:
                if "ERR_NAME_NOT_RESOLVED" in str(e) and attempt < retries - 1:
                    print(f"  ⚠️ DNS 解析失败，重试 {attempt + 2}/{retries}...")
                    await asyncio.sleep(2)
                else:
                    raise

    async def _human_delay(self):
        delay = random.triangular(self.min_interval, self.max_interval, self.min_interval + 0.3)
        await asyncio.sleep(delay)

    async def wait_random(self, min_s: float = None, max_s: float = None):
        min_s = min_s or self.min_interval
        max_s = max_s or self.max_interval
        delay = random.triangular(min_s, max_s, min_s + (max_s - min_s) * 0.3)
        await asyncio.sleep(delay)

    async def wait_for_selector(self, selector: str, timeout: int = None) -> bool:
        if not self.page:
            return False
        try:
            await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
            return True
        except Exception:
            return False

    async def evaluate(self, expression: str):
        if not self.page:
            return None
        return await self.page.evaluate(expression)

    async def screenshot(self, path: str = None):
        if not self.page:
            return None
        return await self.page.screenshot(path=path)

    async def query_selector(self, selector: str):
        if not self.page:
            return None
        return await self.page.query_selector(selector)

    async def query_selector_all(self, selector: str):
        if not self.page:
            return []
        return await self.page.query_selector_all(selector)
