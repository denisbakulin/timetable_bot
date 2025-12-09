import asyncio

from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.data import ADMIN_TEXT
from app.db.user import UserService
from app.filters.default import IsAdminFilter
from app.fsm.default import Waiting
from app.keyboards.kb import cancel_kb

router = Router()
router.message.filter(IsAdminFilter())


@router.message(Command("admin"))
async def dist(message: Message):
    await message.answer(ADMIN_TEXT)


@router.message(Command("dist"))
async def dist(message: Message, state: FSMContext):
    await message.answer("Напишите сообщение для рассылки", reply_markup=cancel_kb)
    await state.set_state(Waiting.dist)


@router.message(Command("users"))
async def users(message: Message):
    groups = await UserService().get_user_groups()
    users = await UserService().get_any_by()
    await message.answer(
        f"Всего пользователей: {len(users)}\n{'\n'.join(f'{group}: {count}' for group, count in groups)}",
    )

@router.message(StateFilter(Waiting.dist))
async def dist_send(message: Message, bot: Bot, state: FSMContext):
    ids = await UserService().get_all_ids()

    sent = 0  # сколько сообщений реально доставлено

    async def safe_send(uid: int):
        nonlocal sent
        try:
            await bot.send_message(uid, f"🔔 Уведомление [рассылка]\n\n{message.text}")
            sent += 1
        except Exception:
            ...


    tasks = [asyncio.create_task(safe_send(uid)) for uid in ids]

    await asyncio.gather(*tasks)

    await state.clear()
    await message.answer(f"Рассылка отправлена  {sent}/{len(ids)} раз ({sent / len(ids) *100 }%).")


