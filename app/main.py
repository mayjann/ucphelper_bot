import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from modules.bot import AuthStates, auth, Scheduler, create_auth_router
from modules.browser import BrowserSession, AuthBrowser, UCPBrowser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_TG_ID = int(os.getenv("ALLOWED_TG_ID"))
UCP_CHAT_ID = int(os.getenv("UCP_CHAT_ID"))
MSG_STATUS_ID = int(os.getenv("MSG_STATUS_ID"))


bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


session = BrowserSession()
auth_browser = AuthBrowser(session)
ucp_browser = UCPBrowser(session)


async def main():
    await session.init()

    auth_router = create_auth_router(auth_browser, user_id=ALLOWED_TG_ID)
    dp.include_router(auth_router)

    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))

    ucp_scheduler = Scheduler(
        bot=bot,
        dp=dp,
        check_ucp=ucp_browser.check_ucp,
        auth_state=AuthStates,
        user_id=ALLOWED_TG_ID,
        chat_id=UCP_CHAT_ID,
        msg_id=MSG_STATUS_ID,
    )

    ucp_scheduler.setup(scheduler, ZoneInfo("Europe/Moscow"))
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())