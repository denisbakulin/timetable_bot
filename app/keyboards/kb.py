from aiogram.types import (BotCommand, InlineKeyboardButton,
                           InlineKeyboardMarkup)
from aiogram.filters.callback_data import CallbackData
from app.client.api import Week

cmd_list = [
    ("/start", "Начать"),
    ("/menu", "Главное меню"),
    ("/today", "Расписание на сегодня"),
    ("/timetable", "Расписание"),
    ("/settings", "Настройки"),
    ("/feedback", "Обратная связь"),
    ("/admin", "Админка"),
]


admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(callback_data="users", text="Пользователи")],
    ]
)

back_admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(callback_data="admin", text="Админ Панель")]
    ]
)


users_admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(callback_data="users_info", text="Список")],
    ] + back_admin_kb.inline_keyboard
)

cancel_kb = (
    InlineKeyboardMarkup(
        inline_keyboard=[
         [InlineKeyboardButton(text=f"Отмена", callback_data="delete")]
        ]
    )
)





main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Главное Меню", callback_data="menu")]
    ]
)

menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🕒 Расписание", callback_data="timetable")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ]
)

cmd_menu = [
    BotCommand(command=cmd, description=desk)
    for cmd, desk in cmd_list
]


from datetime import datetime
class TimetableCallback(CallbackData, prefix="timetable"):
    action: str
    n: int | None = None
    day: str | None = None
    updated: int | None = None
    all: bool = False



def create_tt_kb(
        callback_data: TimetableCallback
) -> InlineKeyboardMarkup:
    callback_data.updated = int(datetime.now().timestamp())
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=TimetableCallback(
                    **dict(**callback_data.dict())
                ).pack()
            )],
            [InlineKeyboardButton(text="« Назад", callback_data="timetable")]
        ]
    )
    return kb



days = {
    'Понедельник': 0,
    'Вторник': 1,
    'Среда': 2,
    'Четверг': 3,
    'Пятница': 4,
    'Суббота': 5,
    'Воскресенье': 6
}


def create_week_kb(week: Week, callback_data):

    # Кнопка "Все расписание" с выравниванием
    all_week = [[InlineKeyboardButton(
        text="📊 Все расписание",
        callback_data=TimetableCallback(
            action="week",
            all=True,
            n=week.number
        ).pack()
    )]]

    # Кнопки дней с выравниванием
    kb = [
        [InlineKeyboardButton(
            text=day.name,
            callback_data=TimetableCallback(
                action="week",
                day=day.name,
                n=week.number
            ).pack())]
        for day in week.days
    ]

    week_kb = InlineKeyboardMarkup(
        inline_keyboard=kb + all_week + create_tt_kb(callback_data).inline_keyboard
    )

    return week_kb

main_timetable_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✨ Сегодня", callback_data=TimetableCallback(action="today").pack())],
        [InlineKeyboardButton(text="📋 1-я неделя", callback_data=TimetableCallback(action="week", n=0).pack()),
         InlineKeyboardButton(text="📋 2-я неделя", callback_data=TimetableCallback(action="week", n=1).pack())],
        [InlineKeyboardButton(text="🏠 Главная", callback_data=TimetableCallback(action="cancel").pack())]

])




def create_settings_kb(user):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔕 Отписаться" if user.subscribe else "🔔 Подписаться", callback_data="subscribe")],
            [InlineKeyboardButton(text="🔄 Изменить группу", callback_data="change_group")],
            [InlineKeyboardButton(text="⏰ Время отправки расписания", callback_data="change_notify_time")],
            [InlineKeyboardButton(text="« Назад", callback_data="menu")]
        ]
    )
