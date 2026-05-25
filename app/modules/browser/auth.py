from playwright.async_api import TimeoutError

class AuthBrowser:
    def __init__(self, session):
        self.session = session

    async def start_login(self, login: str, password: str):
        page = await self.session.context.new_page()

        await page.goto("https://admin.gambit-rp.com/account/login")

        await page.fill('input[name="login"]', login)
        await page.fill('input[name="password"]', password)

        await page.click('button[type="submit"]')

        try:
            await page.wait_for_selector('input[name="emailcode"]', timeout=10000)
            self.session.page = page
            return "NEED_CODE"
        except TimeoutError:
            await self.session.context.storage_state(path="state.json")
            self.session.page = page
            return "OK"

    async def submit_code(self, code: str):
        page = self.session.page

        await page.fill('input[name="emailcode"]', code)
        await page.click('button[type="submit"]')

        await page.wait_for_load_state("networkidle")
        await self.session.context.storage_state(path="state.json")

        return "OK"