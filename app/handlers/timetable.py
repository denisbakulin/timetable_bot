from aiogram import F, Router

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.base import User, UserService, UserSchema
from app.fsm.default import Waiting
from app.keyboards.kb import main_timetable_kb, cancel_kb, create_tt_kb, create_week_kb, main_menu_kb
from app.handlers.menu import create_menu_message
from app.client.api import PalladaClient

from datetime import datetime
from app.client.api import format_day

from app.keyboards.kb import TimetableCallback

from datetime import datetime
router = Router()


async def process_user_timetable(message: Message, user: UserSchema, state: FSMContext, new: bool = False):
    if user.group is None:
        await state.set_state(Waiting.group)
        await message.answer(
            "Укажите название группы",
            reply_markup=cancel_kb
        )
    else:
        func = message.answer if new else message.edit_text

        await func(
            f"⌛ Расписание для группы {user.group}",
            reply_markup=main_timetable_kb
        )

@router.message(Command("timetable"))
async def timetable(message: Message, state: FSMContext):
    user = await UserService().get_user_by_tg_id(message.from_user.id)

    await process_user_timetable(message, user, state, new=True)


@router.callback_query(F.data == "timetable")
async def timetable_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    await process_user_timetable(callback.message, user, state)





@router.callback_query(TimetableCallback.filter(F.action == "cancel"))
async def cancel_timetable(callback: CallbackQuery):
    await callback.answer()
    await create_menu_message(callback.message, callback.from_user.id, edit=True)



@router.message(Command("today"))
async def get_today_cmd(message: Message, state: FSMContext):
    user = await UserService().get_user_by_tg_id(message.from_user.id)

    if user.group is None:
        return await process_user_timetable(message, user, state, new=True)
    timetable = await PalladaClient().get_today_timetable(user.group)

    await message.answer(
        timetable,
        parse_mode="HTML",
        reply_markup=main_menu_kb
    )

def format_edited_message(main: str, updated: int) -> str:
    upd = f"\n<i>Обновлено {datetime.fromtimestamp(updated)}</i>" if updated else ""

    return main + upd

@router.callback_query(TimetableCallback.filter(F.action == "today"))
async def get_today(
        callback: CallbackQuery,
        callback_data: TimetableCallback
):

    await callback.answer()

    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    timetable = await PalladaClient().get_today_timetable(user.group)

    await callback.message.edit_text(
        format_edited_message(timetable, callback_data.updated),
        parse_mode="HTML",
        reply_markup=create_tt_kb(callback_data)
    )

@router.callback_query(TimetableCallback.filter(F.action == "week"))
async def get_week(
        callback: TimetableCallback,
        callback_data: TimetableCallback
):

    await callback.answer()
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    client = PalladaClient()
    week, timetable = await client.get_week_timetable(user.group, callback_data.n)

    if callback_data.all:
        await callback.message.edit_text(
            format_edited_message(timetable, callback_data.updated),
            parse_mode="HTML",
            reply_markup=create_week_kb(week, callback_data)
        )

    elif callback_data.day:
        day = [day for day in week.days if day.name == callback_data.day][0]
        await callback.message.edit_text(
            format_edited_message(format_day(day), callback_data.updated),
            parse_mode="HTML",
            reply_markup=create_week_kb(week, callback_data)
        )
    else:
        await callback.message.edit_text(
            format_edited_message(f"📅 {week.number+1}-я Неделя" , callback_data.updated),
            parse_mode="HTML",
            reply_markup=create_week_kb(week, callback_data)
        )





