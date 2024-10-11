#!/usr/bin/env python
from __future__ import annotations

import asyncio
from pathlib import Path
import random
import sys
from typing import Literal
from playwright.async_api import async_playwright
from superpilot.core.configuration.config import Config, get_config
from superpilot.framework.helpers.logs import logger

config = get_config()

userAgentStrings = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.3497.92 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]


class PlaywrightWrapper:
    """Wrapper around Playwright.

    To use this module, you should have the `playwright` Python package installed and ensure that
    the required browsers are also installed. You can install playwright by running the command
    `pip install metagpt[playwright]` and download the necessary browser binaries by running the
    command `playwright install` for the first time."
    """

    def __init__(
        self,
        browser_type: Literal["chromium", "firefox", "webkit"] | None = None,
        launch_kwargs: dict | None = None,
        **kwargs,
    ) -> None:
        if browser_type is None:
            browser_type = "chromium" or Config.playwright_browser_type
        self.browser_type = browser_type
        launch_kwargs = launch_kwargs or {}
        # # TODO set proxy in config
        # if Config.global_proxy and "proxy" not in launch_kwargs:
        #     args = launch_kwargs.get("args", [])
        #     if not any(str.startswith(i, "--proxy-server=") for i in args):
        #         launch_kwargs["proxy"] = {"server": Config.global_proxy}
        self.launch_kwargs = launch_kwargs
        # self.launch_kwargs["headless"] = False

        context_kwargs = {"user_agent": random.choice(userAgentStrings)}
        # if config.web_proxy:
        #     self.launch_kwargs["proxy"] = {"server": random.choice(config.web_proxy)}
        if "ignore_https_errors" in kwargs:
            context_kwargs["ignore_https_errors"] = kwargs["ignore_https_errors"]
        self._context_kwargs = context_kwargs
        self._has_run_precheck = False

    async def run(self, url: str, *urls: str) -> str | list[str]:
        async with async_playwright() as ap:
            browser_type = getattr(ap, self.browser_type)
            await self._run_precheck(browser_type)
            browser = await browser_type.launch(**self.launch_kwargs)

            async def _scrape(url):
                context = await browser.new_context(**self._context_kwargs)
                page = await context.new_page()
                async with page:
                    try:
                        await page.goto(url)
                        await page.evaluate(
                            "window.scrollTo(0, document.body.scrollHeight)"
                        )
                        content = await page.content()
                        return content
                    except Exception as e:
                        return f"Fail to load page content for {e}"

            if urls:
                return await asyncio.gather(_scrape(url), *(_scrape(i) for i in urls))
            return await _scrape(url)

    async def _run_precheck(self, browser_type):
        if self._has_run_precheck:
            return

        executable_path = Path(browser_type.executable_path)
        if not executable_path.exists() and "executable_path" not in self.launch_kwargs:
            kwargs = {}
            # if Config.global_proxy:
            #     kwargs["env"] = {"ALL_PROXY": Config.global_proxy}
            await _install_browsers(self.browser_type, **kwargs)
            if not executable_path.exists():
                parts = executable_path.parts
                available_paths = list(Path(*parts[:-3]).glob(f"{self.browser_type}-*"))
                if available_paths:
                    logger.warning(
                        "It seems that your OS is not officially supported by Playwright. "
                        "Try to set executable_path to the fallback build version."
                    )
                    executable_path = available_paths[0].joinpath(*parts[-2:])
                    self.launch_kwargs["executable_path"] = str(executable_path)
        self._has_run_precheck = True


async def _install_browsers(*browsers, **kwargs) -> None:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "playwright",
        "install",
        *browsers,
        "--with-deps",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )

    await asyncio.gather(
        _log_stream(process.stdout, logger.info),
        _log_stream(process.stderr, logger.warn),
    )

    if await process.wait() == 0:
        logger.info(f"Install browser for playwright successfully.")
    else:
        logger.warning(f"Fail to install browser for playwright.")


async def _log_stream(sr, log_func):
    while True:
        line = await sr.readline()
        if not line:
            return
        log_func(f"[playwright install browser]: {line.decode().strip()}")


if __name__ == "__main__":
    for i in ("chromium", "firefox", "webkit"):
        text = asyncio.run(PlaywrightWrapper(i).run("https://httpbin.org/ip"))
        print(text)
        print(i)
