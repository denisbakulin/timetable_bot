START_TEXT = (
    "📅 Быстро узнавай расписание с помощью команды /today или '<code>сегодня</code>'.\n\n"

    "ℹ️ Для подробной информации и списка команд используй команду /help.\n\n"

    "👇 Или просто открой главное меню ниже и выбери нужный раздел.\n\n"
)

CHANGE_GROUP_TEXT = (
    "🎓 <b>Укажите название группы</b>\n"                     
    "▫️ Например: <i>БПИ25-02</i>"
)

HELP_TEXT = (
    "📚 <b>Расписание СибГУ</b> - твой помощник в учёбе!\n\n"

    "🧭 <b>Доступные команды:</b>\n\n"

    "🚀 /start - начать работу с ботом\n"
    "🏠 /menu - открыть главное меню\n"
    "🆘 /help - показать это сообщение\n"
    "🔥 /today - расписание на сегодня \n"
    "▶️ /tomorrow - расписание на завтра\n"
    "💬 /feedback - сообщить об ошибке или оставить отзыв\n"
    "ℹ️ /about - о проекте\n\n"

    f"❓ Если бот не отвечает - попробуй /start или свяжись с @Scambrawlgems."
)



FEEDBACK_TEXT = (
    "✉️ Напиши своё сообщение или отзыв."
)

MENU_TEXT = (
    "<b>Главное меню. Добро пожаловать!</b>\n\n"

    "👥 Ваша группа: <b>{group}</b>\n"
    "❓ Есть вопросы? /help\n"
)

SETTINGS_TEXT = (
    "⚙️ <b>Меню настроек</b>\n\n"
    
    "👥 <b>Текущая группа: {group}</b>\n"
    "Установи текущую группу, чтобы получать ее расписание.\n\n"
    
    "🐣 <b>Подгруппа: {subgroup}</b>\n"
    "Установи свою подгруппу для более персонализированного расписания.\n\n"
    
    "🔔 <b>Подписка: {subscription_status}</b>\n"
    "Включи подписку, чтобы получать расписание в установленное время.\n\n"
    
    "⏰ <b>Время отправки расписания: {notify_time:%H:%M}</b>\n"
    "Установи удобное для тебя время, когда бот будет присылать уведомления о занятиях."
)


ADMIN_TEXT = (
    "Админ Панель\n"
    "/admin_help - подсказка по админским командам\n"
    "/proxy - текущий прокси (или установить)\n"
    "/add_group - добавить/обновить группу по pallada id\n"
    "/refresh_group - обновить группу по pallada id\n"
    "/admin_stats - статистика\n"
    "/admin_users - группы по пользователям\n"
    "/admin_groups - интерактив: группы/пользователи\n"
    "/whereami - chat_id/thread_id\n"
    "/health - проверки\n"
    "/dump_config - конфиг\n"
    "/last_refresh - последнее обновление группы\n"
    "/set_cache_ttl - TTL кеша\n"
    "/ban_user, /unban_user\n"
    "/broadcast, /broadcast_all, /broadcast_group"
)


ADMIN_HELP_TEXT = (
    "🛠 <b>Админские команды</b>\n\n"
    "<b>/proxy</b>\n"
    "• показать текущий: <code>/proxy</code>\n"
    "• установить: <code>/proxy 212.113.107.128:36613</code>\n"
    "• выключить: <code>/proxy off</code>\n\n"
    "<b>/add_group</b>\n"
    "• один id: <code>/add_group 13887</code>\n"
    "• диапазон: <code>/add_group 13887-13910</code>\n"
    "• с именем (имя опционально): <code>/add_group БИЭ24-01 13900</code>\n\n"
    "<b>/refresh_group</b>\n"
    "• обновить id/диапазон: <code>/refresh_group 13887-13910</code>\n\n"
    "<b>/admin_stats</b> — статистика по пользователям/группам\n"
    "<b>/admin_users</b> — топ групп по числу пользователей\n\n"
    "<b>/admin_groups</b> — интерактивный список групп и пользователей\n"
    "<b>/group_stats</b> — статистика по группе\n\n"
    "<b>/whereami</b> — показать chat_id и thread_id\n"
    "<b>/health</b> — проверить SQLite/Redis/Pallada\n"
    "<b>/dump_config</b> — вывести текущий конфиг\n"
    "<b>/set_cache_ttl</b> — установить TTL кеша\n"
    "<b>/last_refresh</b> — последнее обновление группы\n"
    "<b>/ban_user</b>, <b>/unban_user</b>\n"
    "<b>/broadcast</b>, <b>/broadcast_all</b>, <b>/broadcast_group</b>\n\n"
    "<b>/admin</b> — короткое меню\n"
)

ABOUT_TEXT = (
    "ℹ️ <b>Информация о проекте</b>\n\n"

    "🛠 <b>Технологии:</b>\n"
    '• <a href="https://www.python.org/downloads/release/python-3120/">Python 3.12</a>\n'
    '• <a href="https://pypi.org/project/aiogram/">Aiogram</a> - Telegram Bot API\n'
    '• <a href="https://pypi.org/project/beautifulsoup4/">Beautiful Soup 4</a> - парсинг HTML\n'
    '• <a href="https://pypi.org/project/APScheduler/">APScheduler</a> - уведомления / отложенные задачи\n\n'
    
    "📮 <b>Обратная связь</b>\n"
    "Нашли ошибку? Есть предложения?\n"
    f"Пишите @Scambrawlgems или /feedback\n"
)

