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
            timetable = await timetable_client.get_today_timetable(user)

            if not user.subscribe:
                return None

            if timetable:
                await bot.send_message(
                    tg_id,
                    f"🔔 Уведомление | Расписание:\n\n{timetable}",
                    parse_mode="HTML",
                    reply_markup=main_menu_kb
                )

            else:
                await bot.send_message(
                    tg_id,
                    "🔔 Уведомление | На сегодня расписания нет или временная ошибка",
                    parse_mode="HTML",
                    reply_markup=main_menu_kb
                )


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

        # Подсос расписаний:
        # - группы с пользователями: ежедневно ночью
        # - группы без пользователей: раз в неделю ночью
        scheduler.add_job(
            PalladaClient().update_timetable_task(),
            "cron",
            hour=3,
            minute=10,
            id="tt-refresh-active",
            replace_existing=True,
        )
        scheduler.add_job(
            PalladaClient().update_timetable_task(inactive=True),
            "cron",
            day_of_week="mon",
            hour=4,
            minute=10,
            id="tt-refresh-inactive",
            replace_existing=True,
        )

        scheduler.start()



notification_manager = NotificationManager()
