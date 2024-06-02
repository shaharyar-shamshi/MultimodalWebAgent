import os
import locale
import logging
from playwright.async_api import async_playwright
from tzlocal import get_localzone_name
from src.configs.logging.logging_config import setup_logging

setup_logging()
logger = logging.getLogger()

class WebDriver:
    __instance = None

    @staticmethod
    async def getInstance(*args, **kwargs):
        if WebDriver.__instance is None:
            WebDriver.__instance = WebDriver(*args, **kwargs)
            await WebDriver.__instance.createDriver(*args, **kwargs)
        return WebDriver.__instance

    def __init__(self, *args, **kwargs):
        if WebDriver.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            WebDriver.__instance = self
            self.playwright = None
            self.browser = None
            self.page = None

    async def ensure_playwright_browsers_installed(self, playwright):
        browsers_path = playwright.__dict__.get("browsers_path")
        if not os.path.exists(browsers_path):
            await playwright.install()

    async def createDriver(self, *args, **kwargs):
        timezone_id = get_localzone_name()
        system_locale = locale.getdefaultlocale()

        try:
            playwright = await async_playwright().start()
            await self.ensure_playwright_browsers_installed(playwright)
            browser = await playwright.chromium.launch_persistent_context(
                user_data_dir="/tmp/chrome_profile",  # Use /tmp directory
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-web-security",
                    "--allow-running-insecure-content",
                ],
                locale=system_locale[0],
                timezone_id=timezone_id,
            )
            self.playwright = playwright
            self.browser = browser
            self.page = await browser.new_page()
            await self.page.set_viewport_size({"width": 960, "height": 1080})
            logger.info("Browser instance created successfully.")
        except Exception as e:
            logger.error("Failed to create browser instance.", exc_info=True)
            raise e

    async def getDriver(self):
        if self.browser is None:
            await self.createDriver()
        return self.page

    async def closeDriver(self):
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser instance closed successfully.")
        except Exception as e:
            logger.error("Failed to close browser instance.", exc_info=True)
            raise e

    async def closeCurrentTab(self):
        if self.page and not self.page.is_closed():
            try:
                await self.page.close()
                self.page = await self.browser.new_page()
                await self.page.set_viewport_size({"width": 960, "height": 1080})
                logger.info("Current tab closed successfully.")
            except Exception as e:
                logger.error("Failed to close current tab.", exc_info=True)
                raise e
