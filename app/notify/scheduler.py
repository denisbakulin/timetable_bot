from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from app.settings import bot_settings
from app.client.api import PalladaClient
from app.db.base import UserService
from app.keyboards.kb import main_menu_kb
import asyncio

scheduler = AsyncIOScheduler()


class NotificationManager:
    def __init__(self):
        self._bot = None

    @property
    def bot(self) -> Bot:
        if self._bot is None:
            self._bot = Bot(token=bot_settings.token)
        return self._bot

    def create_task(self, tg_id: int):


        async def wrapper():
            # Создаем нового бота для каждой задачи
            bot = Bot(token=bot_settings.token)



            user = await UserService().get_user_by_tg_id(tg_id)

            timetable_client = PalladaClient()
            timetable = await timetable_client.get_today_timetable(user.group)

            if timetable:
                await bot.send_message(
                    tg_id,
                    f"🔔 Уведомление | Расписание:\n\n{timetable}",
                    parse_mode="HTML",
                    reply_markup=main_menu_kb
                )
                print(f"✅ Уведомление отправлено пользователю {tg_id}")
            else:
                await bot.send_message(
                    tg_id,
                    "🔔 Уведомление | На сегодня расписания нет или временная ошибка",
                    reply_markup=main_menu_kb
                )
                print(f"ℹ️  Пользователю {tg_id} отправлено сообщение об отсутствии расписания")


            print(f"🔚 Завершена обработка пользователя {tg_id}")

        return wrapper

    async def close(self):
        if self._bot:
            await self._bot.session.close()


# Глобальный экземпляр
notification_manager = NotificationManager()