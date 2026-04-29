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

]

cmd_menu = [
    BotCommand(command=cmd, description=desk)
    for cmd, desk in cmd_list
]

subgroups_dict = {
    "🌐": 0,
    "1": 1,
    "2": 2,
}

cancel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
     [InlineKeyboardButton(text=f"Отмена", callback_data="delete")]
    ]
)


main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Главное Меню", callback_data="menu")]
    ]
)


class TimetableCallback(CallbackData, prefix="timetable"):
    action: str
    n: int | None = None
    day: str | None = None
    updated: int | None = None
    all: bool = False


menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🕒 Расписание", callback_data="timetable"),
            InlineKeyboardButton(
                text="Ленты",
                callback_data=TimetableCallback(action="next_lesson").pack(),
            ),
        ],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ]
)



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
                    **callback_data.dict()
                ).pack()
            )]
        ]
    )
    return kb


def create_next_lesson_kb(current_index: int, total: int) -> InlineKeyboardMarkup:
    nav_row = []
    if current_index > 0:
        nav_row.append(
            InlineKeyboardButton(
                text="◀️ Предыдущая",
                callback_data=TimetableCallback(action="next_lesson", n=current_index - 1).pack(),
            )
        )


    if current_index < total - 1:
        nav_row.append(
            InlineKeyboardButton(
                text="Следующая ▶️",
                callback_data=TimetableCallback(action="next_lesson", n=current_index + 1).pack(),
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav_row,
            [
                InlineKeyboardButton(
                    text="🔄 Ближайшая",
                    callback_data=TimetableCallback(action="next_lesson").pack(),
                ),
                InlineKeyboardButton(text="🏠 Главная", callback_data="menu"),
            ],
        ]
    )


about_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="github", url="https://github.com/denisbakulin/timetable_bot")]
    ] + main_menu_kb.inline_keyboard
)


def check_sub_lessons(day: Day) -> bool:
    flag = False
    for lesson in day.lessons:
        flag = flag or bool(lesson.sub_lessons)
        if flag:
            return True
    return False

def format_week_day_name(week: Week, day: Day) -> str:
    if not week.current:
        return day.name

    if day.name == weekdays[datetime.now().weekday()]:
        return f"⭐️ {day.name}"

    return day.name


def create_week_kb(week: Week, callback_data):

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

        [InlineKeyboardButton(text="📋 1-я / нечет", callback_data=TimetableCallback(action="week", n=0).pack()),
         InlineKeyboardButton(text="📋 2-я / чет", callback_data=TimetableCallback(action="week", n=1).pack())],
        [InlineKeyboardButton(text="⭐ Избранные группы", callback_data="favorite_groups_timetable")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data=TimetableCallback(action="cancel").pack())]

])


class SubGroupCallback(CallbackData, prefix="subgroup"):
    n: int


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
            [InlineKeyboardButton(text="⭐ Избранные группы", callback_data="favorite_groups")],
            [InlineKeyboardButton(text="🧩 Изменить подгруппу", callback_data="change_subgroup")],
            [InlineKeyboardButton(text="⏰ Время отправки расписания", callback_data="change_notify_time")],
            [InlineKeyboardButton(text="⏳ Напоминание до пары", callback_data="change_lesson_notify")],
            [InlineKeyboardButton(text="« Назад", callback_data="menu")]
        ]
    )


class LessonNotifyCallback(CallbackData, prefix="lesson_notify"):
    minutes: int


def create_lesson_notify_kb(current_minutes: int) -> InlineKeyboardMarkup:
    minutes_list = [0, 5, 10, 15, 30]
    buttons = []

    for minutes in minutes_list:
        title = "Выключено" if minutes == 0 else f"{minutes} мин"
        if current_minutes == minutes:
            title = f"✅ {title}"
        buttons.append(
            InlineKeyboardButton(
                text=title,
                callback_data=LessonNotifyCallback(minutes=minutes).pack(),
            )
        )

    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="settings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


class FavoriteGroupCallback(CallbackData, prefix="favorite_group"):
    action: str
    group_id: int
    source: str = "settings"


def create_favorite_groups_kb(
    favorites,
    current_group_id: int | None,
    *,
    source: str,
    remove_mode: bool = False,
) -> InlineKeyboardMarkup:
    rows = []

    for favorite in favorites:
        group = favorite.group
        if remove_mode:
            text = f"❌ {group.name}"
            action = "remove"
        else:
            text = f"✅ {group.name}" if group.pallada_id == current_group_id else f"⭐ {group.name}"
            action = "set"

        rows.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=FavoriteGroupCallback(
                        action=action,
                        group_id=group.pallada_id,
                        source=source,
                    ).pack(),
                )
            ]
        )

    if source == "settings":
        rows.append([InlineKeyboardButton(text="➕ Добавить группу", callback_data="add_favorite_group")])
        if favorites:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="✅ Готово" if remove_mode else "🗑 Удалить группу",
                        callback_data="favorite_groups" if remove_mode else "favorite_groups_remove",
                    )
                ]
            )
        rows.append([InlineKeyboardButton(text="« Назад", callback_data="settings")])
    elif source == "change_group":
        rows.append([InlineKeyboardButton(text="✍️ Ввести другую группу", callback_data="change_group_manual")])
        rows.append([InlineKeyboardButton(text="« Назад", callback_data="settings")])
    else:
        rows.append([InlineKeyboardButton(text="⚙️ Управление", callback_data="favorite_groups")])
        rows.append([InlineKeyboardButton(text="« Назад", callback_data="timetable")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


class AdminGroupsCallback(CallbackData, prefix="admin_groups"):
    page: int


class AdminGroupUsersCallback(CallbackData, prefix="admin_group_users"):
    pallada_id: int
    page: int = 0


def create_admin_groups_kb(*, page: int, total: int, page_size: int, rows) -> InlineKeyboardMarkup:
    buttons = []
    for pid, name, cnt in rows:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{name} ({cnt})",
                    callback_data=AdminGroupUsersCallback(pallada_id=int(pid), page=0).pack(),
                )
            ]
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="«", callback_data=AdminGroupsCallback(page=page - 1).pack()))
    if (page + 1) * page_size < total:
        nav.append(InlineKeyboardButton(text="»", callback_data=AdminGroupsCallback(page=page + 1).pack()))
    if nav:
        buttons.append(nav)

    if not buttons:
        buttons = [[InlineKeyboardButton(text="« Назад", callback_data="menu")]]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_admin_group_users_kb(*, pallada_id: int, page: int, total: int, page_size: int) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text="← К группам", callback_data=AdminGroupsCallback(page=0).pack())]]

    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton(
                text="«",
                callback_data=AdminGroupUsersCallback(pallada_id=pallada_id, page=page - 1).pack(),
            )
        )
    if (page + 1) * page_size < total:
        nav.append(
            InlineKeyboardButton(
                text="»",
                callback_data=AdminGroupUsersCallback(pallada_id=pallada_id, page=page + 1).pack(),
            )
        )
    if nav:
        kb.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=kb)
