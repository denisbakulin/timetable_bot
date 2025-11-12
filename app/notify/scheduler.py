from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.client.api import PalladaClient
from app.db.user import UserService
from app.keyboards.kb import main_menu_kb
from app.settings import bot_settings

scheduler = AsyncIOScheduler()


class NotificationManager:

    def create_task(self, tg_id: int):


        async def wrapper():
            bot = Bot(token=bot_settings.token)

            user = await UserService().get_user_by_tg_id(tg_id)

            timetable_client = PalladaClient()
            timetable = await timetable_client.get_today_timetable(user.group.name)

            if not user.subscribe:
                return None

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
                    parse_mode="HTML",
                    reply_markup=main_menu_kb
                )
                print(f"ℹ️  Пользователю {tg_id} отправлено сообщение об отсутствии расписания")


            print(f"🔚 Завершена обработка пользователя {tg_id}")

        return wrapper

    async def setup_notify(self):
        users = await UserService().get_any_by()

        for user in users:
            scheduler.add_job(
                notification_manager.create_task(user.tg_id),
                "cron",
                hour=user.notify_time.hour,
                minute=user.notify_time.minute,
                id=str(user.tg_id), replace_existing=True
            )

notification_manager = NotificationManager()