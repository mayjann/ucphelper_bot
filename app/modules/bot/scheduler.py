import asyncio
from .auth_handlers import auth
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from aiogram.exceptions import TelegramBadRequest


class Scheduler:
    STAGNATION_THRESHOLD = 5

    def __init__(self, bot, dp, check_ucp, auth_state, user_id, chat_id, msg_id, logger):
        self.bot = bot
        self.dp = dp
        self.check_ucp = check_ucp
        self.auth_state = auth_state
        self.user_id = user_id
        self.chat_id = chat_id
        self.msg_id = msg_id
        self.logger = logger

        self.stagnation = False
        self.stagnation_first_alert = False
        self.stagnation_tick = 0
        self.global_tick = 0
        self.last_count = 0

    async def _edit(self, count):
        try:
            await self.bot.edit_message_text(chat_id=self.chat_id, message_id=self.msg_id, text=f"[UCP] {count} заявлений")
        except TelegramBadRequest:
            return

    async def _parse(self):
        self.logger.info("Старт проверки UCP")
        res = await self.check_ucp()

        if res == "NO_SESSION":
            self.logger.warning("Нет сессии (NO_SESSION)")

            if auth["awaiting"]:
                return None

            auth["awaiting"] = True

            state = self.dp.fsm.get_context(bot=self.bot, user_id=self.user_id, chat_id=self.user_id)

            await self.bot.send_message(self.user_id, "Сессия слетела\n\nAdmin name:")
            await state.set_state(self.auth_state.login)

            return None

        try:
            return int(res)
        except:
            return 0

    async def job(self):
        count = await self._parse()

        if count is None:
            return

        self.logger.info(f"Количество заявлений: {count}")
        if count != self.last_count:
            await self._edit(count)
            self.last_count = count

        if count >= self.STAGNATION_THRESHOLD and not self.stagnation:
            self.stagnation = True
            self.stagnation_first_alert = False
            self.global_tick = 0
            self.stagnation_tick = 0
            self.logger.warning("Застой начался")
            return

        if count < self.STAGNATION_THRESHOLD:
            if self.stagnation and self.stagnation_first_alert:
                self.logger.info(f"Застой завершён, текущее значение: {count}")
                await self.bot.send_message(self.chat_id, f"[UCP] {count} заявлений. Застой закончился")

            self.stagnation = False
            self.stagnation_first_alert = False
            self.global_tick = 0
            self.stagnation_tick = 0

            self.logger.info("Сброс состояния застоя")
            return

        if self.stagnation:
            self.global_tick += 1
            self.logger.debug(f"global_tick = {self.global_tick}")

            if self.stagnation_first_alert:
                self.stagnation_tick += 1
                self.logger.debug(f"stagnation_tick = {self.stagnation_tick}")

        if self.stagnation and not self.stagnation_first_alert and self.global_tick == 2:
            self.stagnation_first_alert = True

            self.logger.warning("Первое сообщение о застое отправлено")

            await self.bot.send_message(self.chat_id, f"[UCP] {count} заявлений. Застой начался.")

            self.stagnation_tick = 0
            return

        if self.stagnation_first_alert and self.stagnation_tick >= 3:
            self.logger.warning(f"Повторное сообщение о застое (tick={self.stagnation_tick})")

            await self.bot.send_message(self.chat_id, f"[UCP] {count} заявлений. Застой продолжается")

            self.stagnation_tick = 0
            return

    def setup(self, scheduler, timezone):
        trigger = CronTrigger(minute="*/5", timezone=timezone)

        scheduler.add_job(
            self.job,
            trigger=trigger,
            id="ucp_job",
            replace_existing=True,
            max_instances=1,
            next_run_time=datetime.now(timezone)
        )