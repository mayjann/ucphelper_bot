import os
from playwright.async_api import async_playwright

BASE_URL = "https://admin.gambit-rp.com/"

class BrowserSession:
    def __init__(self):
        self.play = None
        self.browser = None
        self.context = None
        self.page = None

    async def init(self):
        self.play = await async_playwright().start()

        self.browser = await self.play.chromium.launch(
            headless=True
        )

        if os.path.exists("state.json"):
            self.context = await self.browser.new_context(storage_state="state.json")
        else:
            self.context = await self.browser.new_context()

    def new_page(self):
        return self.context.new_page()