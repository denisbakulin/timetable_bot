from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.data import CHANGE_GROUP_TEXT
from app.client.api import PalladaClient, format_day, get_current_week, get_today, weekdays
from app.client.formatter import format_lesson, format_week, format_week_title, get_russian_date
from app.db.user import UserSchema, UserService
from app.fsm.default import Waiting
from app.handlers.menu import create_menu_message
from app.keyboards.kb import (TimetableCallback, cancel_kb, create_next_lesson_kb,
                              create_tt_kb, create_week_kb, main_menu_kb,
                              main_timetable_kb)


router = Router()


@router.callback_query(F.data == "delete")
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()


async def process_user_timetable(message: Message, user: UserSchema, state: FSMContext, new: bool = False):
    if user.group is None:
        await state.set_state(Waiting.group)
        await message.answer(
            CHANGE_GROUP_TEXT,
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
    else:
        func = message.answer if new else message.edit_text
        client = PalladaClient()
        tt = await client._get_timetable(user.group.name)
        tt = client.user_timetable(user, tt)

        if not tt or not tt.weeks:
            return await func(
            f"Расписание для группы {user.group} нет😬",
            reply_markup=main_menu_kb
        )

        today = weekdays[datetime.now().weekday()]
        current_week = get_current_week(tt)
        week_title = format_week_title(current_week.number) if current_week else "неделя не определена"

        await func(
            f"⌛ Расписание для группы {user.group.name}\n"  
            f"🔥 Сегодня: {week_title}, {today}",
            reply_markup=main_timetable_kb
        )


@router.callback_query(F.data == "timetable")
async def timetable_callback(callback: CallbackQuery, state: FSMContext):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    await process_user_timetable(callback.message, user, state)



@router.callback_query(TimetableCallback.filter(F.action == "cancel"))
async def cancel_timetable(callback: CallbackQuery):
    await create_menu_message(callback.message, callback.from_user.id, edit=True)



@router.message(Command("today"))
@router.message(F.text.lower().in_(["седня", "сегодня"]))
async def get_today_cmd(message: Message, state: FSMContext):
    user = await UserService().get_user_by_tg_id(message.from_user.id)

    if user.group is None:
        return await process_user_timetable(message, user, state, new=True)

    timetable = await PalladaClient().get_today_timetable(user)

    await message.answer(
        timetable,
        reply_markup=create_tt_kb(TimetableCallback(action="today"))
    )

@router.message(Command("tomorrow"))
@router.message(F.text.lower() == "завтра")
async def get_tomorrow_cmd(message: Message, state: FSMContext):
    user = await UserService().get_user_by_tg_id(message.from_user.id)

    if user.group is None:
        return await process_user_timetable(message, user, state, new=True)

    timetable = await PalladaClient().get_tomorrow_timetable(user)

    await message.answer(
        timetable,
        reply_markup=create_tt_kb(TimetableCallback(action="tomorrow"))
    )

@router.callback_query(TimetableCallback.filter(F.action == "today"))
async def get_today_callback(
        callback: CallbackQuery,
        callback_data: TimetableCallback
):

    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    timetable = await PalladaClient().get_today_timetable(user)

    await callback.message.edit_text(
        format_edited_message(timetable, callback_data.updated),
        reply_markup=create_tt_kb(callback_data)
    )


def format_edited_message(main: str, updated: int) -> str:
    upd = f"\n<i>Обновлено {datetime.fromtimestamp(updated)}</i>" if updated else ""

    return main + upd


def get_day_lessons(day) -> list:
    return [lesson for lesson in day.lessons if lesson.sub_lessons]


def get_relevant_lesson_index(lessons: list) -> tuple[int, str]:
    now = datetime.now().time()

    for index, lesson in enumerate(lessons):
        start = datetime.strptime(lesson.start, "%H:%M").time()
        end = datetime.strptime(lesson.end, "%H:%M").time()

        if start <= now <= end:
            return index, "🟢 Сейчас идет"
        if now < start:
            return index, "⏭ Следующая пара"

    return len(lessons) - 1, "✅ На сегодня пары закончились"


def build_next_lesson_text(user: UserSchema, day, lessons: list, index: int, title: str) -> str:
    lesson = lessons[index]
    lesson_text = format_lesson(lesson)

    return (
        f"{title}\n"
        f"👥 Группа: <b>{user.group.name}</b>\n"
        f"📅 <b>{get_russian_date()}</b>\n"
        f"🔢 Пара <b>{index + 1} из {len(lessons)}</b>\n\n"
        f"{lesson_text}"
    )


async def process_next_lesson(
        message: Message,
        user: UserSchema,
        state: FSMContext,
        *,
        selected_index: int | None = None,
):
    if user.group is None:
        return await process_user_timetable(message, user, state, new=True)

    client = PalladaClient()
    timetable = await client._get_timetable(user.group.name)
    timetable = client.user_timetable(user, timetable)

    if not timetable:
        return await message.edit_text(
            "Расписание сейчас недоступно 😬",
            reply_markup=main_menu_kb,
        )

    day = get_today(timetable)
    if day is None:
        return await message.edit_text(
            "❌ Не удалось определить расписание на сегодня",
            reply_markup=main_menu_kb,
        )

    lessons = get_day_lessons(day)
    if not lessons:
        return await message.edit_text(
            "❌ На сегодня занятий нет",
            reply_markup=main_menu_kb,
        )

    if selected_index is None:
        current_index, status = get_relevant_lesson_index(lessons)
        title = f"{status}\n"
    else:
        current_index = max(0, min(selected_index, len(lessons) - 1))
        title = "⏭ <b>Навигация по парам</b>\n"

    await message.edit_text(
        build_next_lesson_text(user, day, lessons, current_index, title),
        reply_markup=create_next_lesson_kb(current_index, len(lessons)),
    )


@router.callback_query(TimetableCallback.filter(F.action == "tomorrow"))
async def get_tomorrow_callback(
        callback: CallbackQuery,
        callback_data: TimetableCallback
):

    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    timetable = await PalladaClient().get_tomorrow_timetable(user)

    await callback.message.edit_text(
        format_edited_message(timetable, callback_data.updated),
        reply_markup=create_tt_kb(callback_data)
    )


@router.callback_query(TimetableCallback.filter(F.action == "next_lesson"))
async def get_next_lesson_callback(
        callback: CallbackQuery,
        callback_data: TimetableCallback,
        state: FSMContext,
):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    await process_next_lesson(
        callback.message,
        user,
        state,
        selected_index=callback_data.n,
    )

@router.callback_query(TimetableCallback.filter(F.action == "week"))
async def get_week(
        callback: CallbackQuery,
        callback_data: TimetableCallback
):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    client = PalladaClient()

    timetable = await client._get_timetable(user.group.name)
    timetable = client.user_timetable(user, timetable)


    if not timetable or not timetable.weeks:
        week_timetable = None
    else:
        c_week = get_current_week(timetable)
        week_timetable = timetable.weeks[callback_data.n]
        week_timetable.current = week_timetable.number == c_week.number


    if week_timetable is None:
        await callback.message.edit_text(
            f"Расписание для группы {user.group} нет😬",
            reply_markup=create_tt_kb(callback_data)
        )

    elif callback_data.all:
        await callback.message.edit_text(
            format_edited_message(format_week(week_timetable), callback_data.updated),
            reply_markup=create_week_kb(week_timetable, callback_data)
        )

    elif callback_data.day:
        day = [day for day in week_timetable.days if day.name == callback_data.day][0]
        await callback.message.edit_text(
            format_edited_message(
                f"🕘 {format_week_title(callback_data.n)}, "
                + format_day(day).replace("📅", ""),
                callback_data.updated,
            ),
            reply_markup=create_week_kb(week_timetable, callback_data)
        )
    else:
        await callback.message.edit_text(
            format_edited_message(
                f"📅 Расписание на {format_week_title(week_timetable.number)}",
                callback_data.updated,
            ),
            reply_markup=create_week_kb(week_timetable, callback_data)
        )





