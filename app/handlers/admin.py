import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.data import ADMIN_TEXT
from app.db.user import UserService
from app.db.group import GroupService
from app.filters.default import IsAdminFilter
from app.fsm.default import Waiting
from app.keyboards.kb import admin_kb, back_admin_kb, cancel_kb, users_admin_kb

router = Router()
router.message.filter(IsAdminFilter())



@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Показывает админ панель"""

    await message.answer(
        ADMIN_TEXT,
        reply_markup=admin_kb
    )


@router.callback_query(F.data == "admin")
async def admin_panel_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        ADMIN_TEXT,
        reply_markup=admin_kb
    )



@router.message(Command("dist"), IsAdminFilter())
async def dist(message: Message, state: FSMContext):
    await message.answer("Напишите сообщение для рассылки", reply_markup=cancel_kb)
    await state.set_state(Waiting.dist)

def users_groupby_group(users):
    s = {}
    for user in users:
        s[user.group.name] = s.get(user.group.name, 0) + 1
    return s


@router.callback_query(F.data == "users")
async def users(callback: CallbackQuery):
    users = await UserService().get_any_by()
    users_by_group = users_groupby_group(users)
    await callback.message.edit_text(
        f"Всего пользователей: {len(users)}\n{'\n'.join(f'{group}: {count}' for group, count in users_by_group.items())}",
        reply_markup=users_admin_kb
    )

@router.callback_query(F.data == "users_info")
async def get_users_info(callback: CallbackQuery, bot: Bot):
    users_ids = await UserService().get_all_ids()

    tasks = [bot.get_chat(tg_id) for tg_id in users_ids]
    res = await asyncio.gather(*tasks)

    await callback.message.edit_text(
        text="Список пользователей\n"+"\n".join(f"@{user.username}" if user.username else "" for user in res),
        reply_markup=back_admin_kb
    )


@router.message(StateFilter(Waiting.dist))
async def dist_send(message: Message, bot: Bot, state: FSMContext):
    ids = await UserService().get_all_ids()

    tasks = [asyncio.create_task(bot.send_message(uid, f"🔔 Уведомление [рассылка]\n\n{message.text}")) for uid in ids]
    await asyncio.gather(*tasks)

    await state.clear()
    await message.answer(f"Рассылка была отправлена {len(ids)} раз")


