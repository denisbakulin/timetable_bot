from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.client.api import PalladaClient, get_current_week, get_today
from app.client.formatter import format_lesson, format_week_title
from app.db.user import UserService
from app.keyboards.kb import main_menu_kb
from app.settings import bot_settings

scheduler = AsyncIOScheduler()


class NotificationManager:
    @staticmethod
    def _get_upcoming_lesson(day, minutes_before: int):
        now = datetime.now().replace(second=0, microsecond=0)

        for lesson in day.lessons:
            if not lesson.sub_lessons:
                continue

            lesson_time = datetime.strptime(lesson.start, "%H:%M").time()
            start_at = datetime.combine(now.date(), lesson_time)
            delta_minutes = int((start_at - now).total_seconds() // 60)

            if delta_minutes == minutes_before:
                return lesson

        return None

    def create_task(self, tg_id: int):


        async def wrapper():
            bot = Bot(token=bot_settings.token)
            try:
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
            finally:
                await bot.session.close()


        return wrapper

    async def notify_before_lessons(self):
        bot = Bot(token=bot_settings.token)
        try:
            users = await UserService().get_any_by(subscribe=True)
            timetable_client = PalladaClient()

            for user in users:
                if user.group is None or user.lesson_notify_minutes <= 0:
                    continue

                timetable = await timetable_client._get_timetable(user.group.name)
                timetable = timetable_client.user_timetable(user, timetable)

                if not timetable:
                    continue

                today = get_today(timetable)
                if not today:
                    continue

                lesson = self._get_upcoming_lesson(today, user.lesson_notify_minutes)
                if lesson is None:
                    continue

                notification_key = (
                    f"{datetime.now().date().isoformat()}:"
                    f"{user.group.pallada_id}:{lesson.start}:{user.lesson_notify_minutes}"
                )
                if getattr(user, "last_lesson_notification_key", None) == notification_key:
                    continue

                current_week = get_current_week(timetable)
                week_line = (
                    f"🗓 <b>{format_week_title(current_week.number)}</b>\n"
                    if current_week is not None
                    else ""
                )
                lesson_text = format_lesson(lesson)

                if not lesson_text:
                    continue

                await bot.send_message(
                    user.tg_id,
                    f"⏳ До пары осталось {user.lesson_notify_minutes} мин\n"
                    f"👥 Группа: <b>{user.group.name}</b>\n"
                    f"{week_line}\n"
                    f"{lesson_text}",
                    parse_mode="HTML",
                    reply_markup=main_menu_kb,
                )

                user_row = await UserService().get_user_by_tg_id(user.tg_id)
                await UserService().update(
                    user_row.id,
                    last_lesson_notification_key=notification_key,
                )
        finally:
            await bot.session.close()

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
        scheduler.add_job(
            self.notify_before_lessons,
            "cron",
            second=0,
            id="lesson-reminders",
            replace_existing=True,
        )

        scheduler.start()



notification_manager = NotificationManager()
