from aiogram import Bot, Dispatcher

from app.client.api import PalladaClient
from app.db.base import init_db

from app.db.group import GroupService
from app.filters.default import AnswerCallback
from app.notify.scheduler import notification_manager, scheduler


START_PARSE_GROUP_ID = 13_000
END_PARSE_GROUP_ID = 15_000

async def setup(dp: Dispatcher, bot: Bot):
    from app.handlers.about import router as about_router
    from app.handlers.admin import router as admin_router
    from app.handlers.feedback import router as feedback_router
    from app.handlers.group import init_admins
    from app.handlers.group import router as group_router
    from app.handlers.help import router as help_router
    from app.handlers.menu import router as menu_router
    from app.handlers.settings import router as settings_router
    from app.handlers.start import router as start_router
    from app.handlers.timetable import router as timetable_router


    bot.admins = []

    dp.include_routers(
        feedback_router,
        help_router,
        menu_router,
        start_router,
        timetable_router,
        settings_router,
        admin_router,
        group_router,
        about_router
    )

    #Отвечает на все калбеки
    dp.callback_query.filter(AnswerCallback())

    from app.db.group import Group
    from app.db.user import User

    await init_db()
    await init_admins(bot)

    await notification_manager.setup_notify()


    groups = await GroupService().get_any_by()

    if not groups:
        await PalladaClient().setup_groups(
            START_PARSE_GROUP_ID, END_PARSE_GROUP_ID
        )


    #парсит расписание для зарегистрированных пользователей
    scheduler.add_job(
        PalladaClient().update_timetable_task(),
        "cron", hour=7,
    )

    # парсит расписание всех групп
    scheduler.add_job(
        PalladaClient().update_timetable_task(all_=True),
        "cron", hour=6, day_of_week="mon"
    )



    scheduler.start()


    from app.keyboards.kb import cmd_menu
    await bot.set_my_commands(cmd_menu)




