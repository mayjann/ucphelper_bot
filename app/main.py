import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from modules.bot import AuthStates, auth, Scheduler, create_auth_router
from modules.browser import BrowserSession, AuthBrowser, UCPBrowser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

logger.info("Запуск приложения")

load_dotenv()
logger.info("Загружен .env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_TG_ID = int(os.getenv("ALLOWED_TG_ID"))
UCP_CHAT_ID = int(os.getenv("UCP_CHAT_ID"))
MSG_STATUS_ID = int(os.getenv("MSG_STATUS_ID"))

logger.info("Переменные окружения загружены")

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logger.info("Инициализирован Telegram Bot и Dispatcher")

session = BrowserSession()
auth_browser = AuthBrowser(session)
ucp_browser = UCPBrowser(session)

logger.info("Созданы browser-классы")

async def main():
    logger.info("Инициализация браузерной сессии")
    await session.init()
    logger.info("Браузерная сессия инициализирована")

    auth_router = create_auth_router(auth_browser, user_id=ALLOWED_TG_ID)
    dp.include_router(auth_router)

    logger.info("Роутер авторизации подключен")

    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))

    ucp_scheduler = Scheduler(
        bot=bot,
        dp=dp,
        check_ucp=ucp_browser.check_ucp,
        auth_state=AuthStates,
        user_id=ALLOWED_TG_ID,
        chat_id=UCP_CHAT_ID,
        msg_id=MSG_STATUS_ID,
        logger=logger
    )

    ucp_scheduler.setup(scheduler, ZoneInfo("Europe/Moscow"))
    scheduler.start()

    logger.info("Запуск polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Вход в main()")
    asyncio.run(main())