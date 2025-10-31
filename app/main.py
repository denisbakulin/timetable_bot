import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.db.base import init_db

from app.handlers.group import  init_admins
from app.handlers.private import private_router
from app.keyboards.kb import cmd_menu
from app.settings import bot_settings
from app.db.base import UserService, GroupService
from app.client.api import PalladaClient


logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=bot_settings.token)

bot.admins = []

dp = Dispatcher()


from app.handlers.feedback import router as fr
from app.handlers.help import router as hr
from app.handlers.menu import router as mr
from app.handlers.start import router as sr
from app.handlers.timetable import router as tr
from app.handlers.settings import router as ss
from app.handlers.admin import admin_router
from app.handlers.group import router as gr


from app.notify.scheduler import notification_manager, scheduler

async def main() -> None:
    await init_db()
    await init_admins(bot)
    await bot.set_my_commands(cmd_menu)


    dp.include_routers(
        admin_router,
        private_router,
        sr,
        hr,
        fr,
        mr,
        tr,
        ss,
        gr
    )
    users = await UserService().get_any_by()

    groups = await GroupService().get_any_by()

    if not groups:
        await PalladaClient().setup_groups(13000, 15000)

    for user in users:

        scheduler.add_job(
            notification_manager.create_task(user.tg_id),
            "cron",
            hour=user.notify_time.hour,
            minute=user.notify_time.minute,
            id=str(user.tg_id), replace_existing=True
        )

    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




