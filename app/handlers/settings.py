from datetime import datetime

from aiogram import F, Router
from aiogram.filters import  StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.handlers.timetable import process_user_timetable

from app.data import SETTINGS_TEXT, CHANGE_GROUP_TEXT
from app.db.favorite_group import FavoriteGroupService
from app.db.user import UserService, UserSchema
from app.db.group import GroupService
from app.fsm.default import Waiting
from app.keyboards.kb import (
    cancel_kb, create_settings_kb, main_menu_kb,
    FavoriteGroupCallback,
    LessonNotifyCallback,
    SubGroupCallback,
    change_subgroup_kb,
    create_favorite_groups_kb,
    create_lesson_notify_kb,
)

router = Router()


def format_lesson_notify_minutes(minutes: int) -> str:
    return "выключено" if minutes == 0 else f"за {minutes} мин"


async def ask_group_name(message: Message, state: FSMContext):
    await state.set_state(Waiting.group)
    await message.answer(
        CHANGE_GROUP_TEXT,
        reply_markup=cancel_kb
    )


async def show_favorite_groups(
        message: Message,
        tg_id: int,
        *,
        source: str,
        remove_mode: bool = False,
        selected_group_name: str | None = None,
):
    user = await UserService().get_user_by_tg_id(tg_id)
    favorites = await FavoriteGroupService().list_for_user(user.id)
    if source == "change_group":
        title = "👥 <b>Выбор текущей группы</b>"
        hint = (
            "Выбери группу кнопкой ниже.\n\n"
            if favorites
            else "Пока нет избранных групп. Введи группу вручную кнопкой ниже.\n\n"
        )
    elif source == "settings":
        title = "⭐ <b>Избранные группы</b>"
        hint = (
            "Нажми на группу, чтобы сделать ее текущей.\n\n"
            if not remove_mode
            else "Нажми на группу, чтобы удалить ее из избранного.\n\n"
        )
    else:
        title = "⭐ <b>Быстрый выбор группы</b>"
        hint = "Нажми на группу, чтобы сделать ее текущей.\n\n"

    current_group = user.group.name if user.group else "не выбрана"
    selected_text = (
        f"✅ Выбрана группа: <b>{selected_group_name}</b>\n\n"
        if selected_group_name
        else ""
    )

    await message.edit_text(
        f"{title}\n\n{selected_text}Текущая группа: <b>{current_group}</b>\n\n{hint}",
        reply_markup=create_favorite_groups_kb(
            favorites,
            user.group.pallada_id if user.group else None,
            source=source,
            remove_mode=remove_mode,
        ),
    )


async def send_format_settings_message(
        message: Message,
        user: UserSchema,
):
    await message.edit_text(SETTINGS_TEXT.format(
        subscription_status="✅" if user.subscribe else "❌",
        group=user.group.name if user.group else "не выбрана",
        notify_time=user.notify_time,
        subgroup=user.subgroup if user.subgroup else "🌐",
        lesson_notify_minutes=format_lesson_notify_minutes(user.lesson_notify_minutes),
    ), reply_markup=create_settings_kb(user))


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)

    await send_format_settings_message(callback.message, user)

@router.callback_query(F.data == "change_subgroup")
async def sub_group_callback(
        callback: CallbackQuery,
):
    await callback.message.answer(
   "🧩 <b>Выберите подгруппу</b>\n\n"
    "🌐 - расписание для всех подгрупп \n"
        , reply_markup=change_subgroup_kb)

@router.callback_query(SubGroupCallback.filter())
async def sub_group_process(
        callback: CallbackQuery,
        callback_data: SubGroupCallback
):
    service = UserService()
    user = await service.get_user_by_tg_id(callback.from_user.id)
    await service.update(user.id, subgroup=callback_data.n)


    if callback_data.n == 0:

        msg = "✅ Выбраны все подгруппы"
    else:
        msg = f"✅ Выбрана подгруппа {callback_data.n}"

    await callback.message.edit_text(msg, reply_markup=main_menu_kb)


@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery):

    user = await UserService().process_subscribe(callback.from_user.id)

    await send_format_settings_message(callback.message, user)


@router.callback_query(F.data == "change_notify_time")
async def get_timetable(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Укажите время в формате ЧАСЫ:МИНУТЫ", reply_markup=cancel_kb)
    await state.set_state(Waiting.notify_time)


@router.callback_query(F.data == "change_lesson_notify")
async def change_lesson_notify(callback: CallbackQuery):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    await callback.message.edit_text(
        "⏳ <b>Напоминание до пары</b>\n\nВыбери, за сколько минут присылать напоминание.",
        reply_markup=create_lesson_notify_kb(user.lesson_notify_minutes),
    )


@router.callback_query(LessonNotifyCallback.filter())
async def set_lesson_notify_time(
        callback: CallbackQuery,
        callback_data: LessonNotifyCallback
):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    user = await UserService().update(user.id, lesson_notify_minutes=callback_data.minutes)
    await send_format_settings_message(callback.message, user)


@router.callback_query(F.data == "favorite_groups")
async def favorite_groups(callback: CallbackQuery):
    await show_favorite_groups(callback.message, callback.from_user.id, source="settings")


@router.callback_query(F.data == "favorite_groups_remove")
async def favorite_groups_remove(callback: CallbackQuery):
    await show_favorite_groups(
        callback.message,
        callback.from_user.id,
        source="settings",
        remove_mode=True,
    )


@router.callback_query(F.data == "favorite_groups_timetable")
async def favorite_groups_timetable(callback: CallbackQuery):
    await show_favorite_groups(callback.message, callback.from_user.id, source="timetable")


@router.callback_query(FavoriteGroupCallback.filter(F.action == "set"))
async def set_favorite_group(
        callback: CallbackQuery,
        callback_data: FavoriteGroupCallback,
):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    if user.group and user.group.pallada_id == callback_data.group_id:
        await callback.answer("Эта группа уже выбрана")
        await show_favorite_groups(
            callback.message,
            callback.from_user.id,
            source=callback_data.source,
            selected_group_name=user.group.name,
        )
        return

    group = await GroupService().get_one_by(pallada_id=callback_data.group_id)
    if group is None:
        await callback.answer("Группа не найдена", show_alert=True)
        return

    await UserService().set_group(callback.from_user.id, group)
    await show_favorite_groups(
        callback.message,
        callback.from_user.id,
        source=callback_data.source,
        selected_group_name=group.name,
    )


@router.callback_query(FavoriteGroupCallback.filter(F.action == "remove"))
async def remove_favorite_group(
        callback: CallbackQuery,
        callback_data: FavoriteGroupCallback,
):
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    await FavoriteGroupService().remove_for_user(user.id, callback_data.group_id)
    await show_favorite_groups(
        callback.message,
        callback.from_user.id,
        source=callback_data.source,
        remove_mode=True,
    )


@router.callback_query(F.data == "add_favorite_group")
async def add_favorite_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Waiting.favorite_group)
    await callback.message.answer(
        "Укажите группу, которую нужно добавить в избранное",
        reply_markup=cancel_kb,
    )

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
    user = await UserService().get_user_by_tg_id(callback.from_user.id)
    favorites = await FavoriteGroupService().list_for_user(user.id)

    if not favorites:
        await ask_group_name(callback.message, state)
        return

    await state.clear()
    await show_favorite_groups(callback.message, callback.from_user.id, source="change_group")


@router.callback_query(F.data == "change_group_manual")
async def change_group_manual(callback: CallbackQuery, state: FSMContext):
    await ask_group_name(callback.message, state)


@router.message(StateFilter(Waiting.group))
async def set_group(message: Message, state: FSMContext):
    group = await GroupService().get_one_by(name=message.text.upper())

    if group is None:
        return await message.reply(
            "Группа не найдена, попробуйте еще раз",
            reply_markup=cancel_kb
        )

    user = await UserService().set_group(message.from_user.id, group)

    await message.reply("✅ Текущая группа установлена!")
    await process_user_timetable(message, user, state, new=True)

    await state.clear()


@router.message(StateFilter(Waiting.favorite_group))
async def add_favorite_group_process(message: Message, state: FSMContext):
    group = await GroupService().get_one_by(name=message.text.upper())

    if group is None:
        return await message.reply(
            "Группа не найдена, попробуйте еще раз",
            reply_markup=cancel_kb,
        )

    user = await UserService().get_user_by_tg_id(message.from_user.id)
    await FavoriteGroupService().add_for_user(user.id, group.pallada_id)
    favorites = await FavoriteGroupService().list_for_user(user.id)

    await state.clear()
    await message.answer(
        f"✅ Группа {group.name} добавлена в избранное",
        reply_markup=create_favorite_groups_kb(
            favorites,
            user.group.pallada_id if user.group else None,
            source="settings",
        ),
    )




