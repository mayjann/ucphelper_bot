class UCPBrowser:
    def __init__(self, session):
        self.session = session

    async def check_ucp(self):
        page = await self.session.context.new_page()

        await page.goto("https://admin.gambit-rp.com/ucp")

        if "/account/login" in page.url:
            await page.close()
            return "NO_SESSION"

        rows = await page.locator("#dataTable tbody tr:not(.dataTables_empty)").count()

        empty = await page.locator(".dataTables_empty").count()

        await page.close()

        if rows == 0 or empty > 0:
            return "0"

        return str(rows)