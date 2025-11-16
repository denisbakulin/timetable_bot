from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.data import CHANGE_GROUP_TEXT
from app.client.api import PalladaClient, format_day, get_current_week, weekdays
from app.client.formatter import format_week
from app.db.user import UserSchema, UserService
from app.fsm.default import Waiting
from app.handlers.menu import create_menu_message
from app.keyboards.kb import (TimetableCallback, cancel_kb, create_tt_kb,
                              create_week_kb, main_menu_kb, main_timetable_kb)

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

        await func(
            f"⌛ Расписание для группы {user.group.name}\n"  
            f"🔥 Сегодня - {get_current_week(tt).number+1}-я неделя, {today}",
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
        reply_markup=main_menu_kb
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
        reply_markup=main_menu_kb
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
        week_timetable = timetable.weeks[callback_data.n]
        print(week_timetable.days[-1])

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
            format_edited_message(f"🕘 {callback_data.n+1}-я Неделя, "+format_day(day).replace("📅", ""), callback_data.updated),
            reply_markup=create_week_kb(week_timetable, callback_data)
        )
    else:
        await callback.message.edit_text(
            format_edited_message(f"📅 Расписание на {week_timetable.number+1}-ю Неделю  ", callback_data.updated),
            reply_markup=create_week_kb(week_timetable, callback_data)
        )





