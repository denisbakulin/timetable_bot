from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.client.api import PalladaClient
from app.data import SETTINGS_TEXT
from app.db.base import  UserService, UserSchema
from app.fsm.default import Waiting
from app.keyboards.kb import cancel_kb, create_settings_kb, main_timetable_kb, main_menu_kb

router = Router()


async def send_format_settings_message(
        message: Message,
        user: UserSchema,
        new: bool = False
):
    func = message.answer if new else message.edit_text

    await func(SETTINGS_TEXT.format(
        subscription_status="✅" if user.subscribe else "❌",
        group=user.group,
        notify_time=user.notify_time
    ), reply_markup=create_settings_kb(user), parse_mode="HTML")


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    await send_format_settings_message(callback.message, user)

@router.message(Command("settings"))
async def settings_cmd(message: Message):
    user = await UserService().get_user_by_tg_id(message.from_user.id)

    await send_format_settings_message(message, user, new=True)


@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery):
    await callback.answer()
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
    await callback.answer()
    await state.set_state(Waiting.group)
    await callback.message.answer("Напишите вашу группу", reply_markup=cancel_kb)


@router.message(StateFilter(Waiting.group))
async def set_group(message: Message, state: FSMContext):
    group_exists = await PalladaClient().group_exists(message.text.upper())

    if not group_exists:
        return await message.reply(
            "Группа не найдена, попробуйте еще раз",
            reply_markup=cancel_kb
        )

    user = await UserService().get_user_by_tg_id(message.from_user.id)
    user = await UserService().update(user.id, group=message.text.upper())

    await message.answer(
        f"⌛ Расписание для группы {user.group}",
        reply_markup=main_timetable_kb, parse_mode="HTML"
    )
    await state.clear()




