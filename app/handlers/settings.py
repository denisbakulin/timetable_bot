from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.handlers.timetable import process_user_timetable

from app.data import SETTINGS_TEXT, CHANGE_GROUP_TEXT
from app.db.user import UserService, UserSchema
from app.db.group import GroupService
from app.fsm.default import Waiting
from app.keyboards.kb import (cancel_kb, create_settings_kb,
                              main_timetable_kb)

router = Router()


async def send_format_settings_message(
        message: Message,
        user: UserSchema,
):
    await message.edit_text(SETTINGS_TEXT.format(
        subscription_status="✅" if user.subscribe else "❌",
        group=user.group,
        notify_time=user.notify_time
    ), reply_markup=create_settings_kb(user))


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    await send_format_settings_message(callback.message, user)


@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery):

    user = await UserService().process_subscribe(callback.from_user.id)

    await send_format_settings_message(callback.message, user)


@router.callback_query(F.data == "change_notify_time")
async def get_timetable(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Укажите время в формате ЧАСЫ:МИНУТЫ", reply_markup=cancel_kb)
    await state.set_state(Waiting.notify_time)

from app.notify.scheduler import notification_manager, scheduler


@router.message(StateFilter(Waiting.notify_time))
async def get_notify_time(message: Message, state: FSMContext):
    try:
        notify_time = datetime.strptime(message.text, "%H:%M").time()

        user = await UserService().get_user_by_tg_id(tg_id=message.from_user.id)
        user = await UserService().update(user.id, notify_time=notify_time)

        scheduler.add_job(
            notification_manager.create_task(user.tg_id),
            "cron",
            hour=user.notify_time.hour,
            minute=user.notify_time.minute,
            id=str(user.tg_id),
            replace_existing=True
        )

        await message.reply(f"✅ Время уведомлений установлено на {message.text}!")
        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Некорректный формат времени. Используйте ЧЧ:MM (например, 08:30)",
            reply_markup=cancel_kb
        )


@router.callback_query(F.data == "change_group")
async def change_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Waiting.group)

    await callback.message.answer(
        CHANGE_GROUP_TEXT,
        reply_markup=cancel_kb
    )


@router.message(StateFilter(Waiting.group))
async def set_group(message: Message, state: FSMContext):
    group = await GroupService().get_one_by(name=message.text.upper())

    if group is None:
        return await message.reply(
            "Группа не найдена, попробуйте еще раз",
            reply_markup=cancel_kb
        )

    user = await UserService().get_user_by_tg_id(message.from_user.id)
    user = await UserService().update(user.id, pallada_id=group.pallada_id)

    await message.reply("✅ Текущая группа установлена!")
    await process_user_timetable(message, user, state, new=True)

    await state.clear()




