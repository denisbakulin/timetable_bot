from aiogram.filters.callback_data import CallbackData
from aiogram.types import (BotCommand, InlineKeyboardButton,
                           InlineKeyboardMarkup)

from app.client.api import Week, Day
from app.client.formatter import weekdays

from datetime import datetime


cmd_list = [
    ("/menu", "Главное меню"),
    ("/today", "Расписание на сегодня"),
    ("/tomorrow", "Расписание на завтра"),
    ("/feedback", "Обратная связь"),
    ("/about", "О проекте")
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
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ]
)

cmd_menu = [
    BotCommand(command=cmd, description=desk)
    for cmd, desk in cmd_list
]


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
            [InlineKeyboardButton(text="« Назад", callback_data="timetable"),
             InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=TimetableCallback(
                    **dict(**callback_data.dict())
                ).pack()
            )]

        ]
    )
    return kb



def format_week_day_name(week: Week, day: Day) -> str:
    if not week.current:
        return day.name

    if day.name == weekdays[datetime.now().weekday()]:
        return f"⭐️ {day.name}"

    return day.name

def create_week_kb(week: Week, callback_data):
    def check_sub_lessons(day: Day) -> bool:
        flag = False
        for lesson in day.lessons:
            flag = flag or bool(lesson.sub_lessons)
            if flag:
                return True
        return False

    days_buttons = []
    for day in week.days:
        if check_sub_lessons(day):
            days_buttons.append(InlineKeyboardButton(
                text=format_week_day_name(week, day),
                callback_data=TimetableCallback(
                    action="week",
                    day=day.name,
                    n=week.number
                ).pack()
            ))

    days_keyboard = []
    
    for i in range(0, len(days_buttons), 2):
        row = days_buttons[i:i + 2]
        days_keyboard.append(row)



    # Кнопка "Все расписание"
    all_week = [[InlineKeyboardButton(
        text="📊 Все расписание",
        callback_data=TimetableCallback(
            action="week",
            all=True,
            n=week.number
        ).pack()
    )]]



    week_kb = InlineKeyboardMarkup(
        inline_keyboard=days_keyboard + all_week + create_tt_kb(callback_data).inline_keyboard
    )

    return week_kb

main_timetable_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✨ Сегодня", callback_data=TimetableCallback(action="today").pack()),
         InlineKeyboardButton(text="🕒 Завтра", callback_data=TimetableCallback(action="tomorrow").pack())],

        [InlineKeyboardButton(text="📋 1-я неделя", callback_data=TimetableCallback(action="week", n=0).pack()),
         InlineKeyboardButton(text="📋 2-я неделя", callback_data=TimetableCallback(action="week", n=1).pack())],
        [InlineKeyboardButton(text="🏠 Главная", callback_data=TimetableCallback(action="cancel").pack())]

])


class SubGroupCallback(CallbackData, prefix="subgroup"):
    n: int

subgroups_dict = {
    "🌐": 0,
    "1": 1,
    "2": 2,
}

change_subgroup_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text=key,
            callback_data=SubGroupCallback(n=value).pack()
        ) for key, value in subgroups_dict.items()]
    ] + cancel_kb.inline_keyboard
)
def create_settings_kb(user):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔕 Отписаться" if user.subscribe else "🔔 Подписаться", callback_data="subscribe")],
            [InlineKeyboardButton(text="🔄 Изменить группу", callback_data="change_group")],
            [InlineKeyboardButton(text="🧩 Изменить подгруппу", callback_data="change_subgroup")],
            [InlineKeyboardButton(text="⏰ Время отправки расписания", callback_data="change_notify_time")],
            [InlineKeyboardButton(text="« Назад", callback_data="menu")]
        ]
    )
