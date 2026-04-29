import asyncio
from aiogram import Bot, Dispatcher

from app.client.api import PalladaClient
from app.db.base import init_db
from app.db.config import AppConfigService  # registers model for create_all
from app.db.ban import BanService  # registers model for create_all
from app.db.group_refresh import GroupRefreshService  # registers model for create_all
from app.db.favorite_group import FavoriteGroupService  # registers model for create_all

from app.filters.default import AnswerCallback
from app.notify.scheduler import notification_manager
from app.utils.proxy import normalize_proxy
from app.middlewares.ban import BanMiddleware



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
    from app.handlers.proxy import router as proxy_router
    from app.handlers.admin_extra import router as admin_extra_router
    from app.settings import bot_settings
    from app.keyboards.kb import cmd_menu

    bot.admins = []

    dp.include_routers(
        admin_router,
        admin_extra_router,
        feedback_router,
        help_router,
        menu_router,
        start_router,
        timetable_router,
        settings_router,
        group_router,
        about_router,
        proxy_router,
    )


    #Отвечает на все калбеки
    dp.callback_query.filter(AnswerCallback())
    dp.message.middleware(BanMiddleware())
    dp.callback_query.middleware(BanMiddleware())

    from app.db.favorite_group import UserFavoriteGroup
    from app.db.group import Group
    from app.db.user import User

    # инициализация моделей
    await init_db()

    # Load saved runtime config from SQLite (survives restarts).
    saved_proxy = await AppConfigService().get_value("timetable_proxy")
    bot_settings.timetable_proxy = normalize_proxy(saved_proxy)

    saved_ttl = await AppConfigService().get_value("timetable_update_time_seconds")
    if saved_ttl and saved_ttl.isdigit():
        bot_settings.timetable_update_time_seconds = int(saved_ttl)

    # Не блокируем запуск бота долгим первичным парсингом списка групп.
    asyncio.create_task(PalladaClient.init())
    # определение админов
    await init_admins(bot)

    # загрузка всех групп


    # фоновые задачи и уведомления
    await notification_manager.setup_notify()

    # установка команд
    await bot.set_my_commands(cmd_menu)




