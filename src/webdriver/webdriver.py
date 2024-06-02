import os
import locale
import logging
import subprocess
from playwright.sync_api import sync_playwright
from tzlocal import get_localzone_name
from src.configs.logging.logging_config import setup_logging

setup_logging()
logger = logging.getLogger()

class WebDriver:
    __instance = None

    @staticmethod
    def getInstance(*args, **kwargs):
        if WebDriver.__instance is None:
            WebDriver.__instance = WebDriver(*args, **kwargs)
            WebDriver.__instance.createDriver(*args, **kwargs)
        return WebDriver.__instance

    def __init__(self, *args, **kwargs):
        if WebDriver.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            WebDriver.__instance = self
            self.playwright = None
            self.browser = None
            self.page = None

    def ensure_playwright_installed(self):
        try:
            # Check if Playwright is already installed by trying to import it
            import playwright
        except ImportError:
            logger.info("Playwright not installed. Installing...")
            subprocess.run(["pip", "install", "playwright"], check=True)
            subprocess.run(["playwright", "install"], check=True)
            logger.info("Playwright installed successfully.")

    def createDriver(self, *args, **kwargs):
        timezone_id = get_localzone_name()
        system_locale = locale.getdefaultlocale()

        try:
            self.ensure_playwright_installed()
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch_persistent_context(
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
            self.page = browser.new_page()
            self.page.set_viewport_size({"width": 960, "height": 1080})
            logger.info("Browser instance created successfully.")
        except Exception as e:
            logger.error("Failed to create browser instance.", exc_info=True)
            raise e

    def getDriver(self):
        if self.browser is None:
            self.createDriver()
        return self.page

    def closeDriver(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser instance closed successfully.")
        except Exception as e:
            logger.error("Failed to close browser instance.", exc_info=True)
            raise e

    def closeCurrentTab(self):
        if self.page and not self.page.is_closed():
            try:
                self.page.close()
                self.page = self.browser.new_page()
                self.page.set_viewport_size({"width": 960, "height": 1080})
                logger.info("Current tab closed successfully.")
            except Exception as e:
                logger.error("Failed to close current tab.", exc_info=True)
                raise e
