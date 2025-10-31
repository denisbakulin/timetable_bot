from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.filters.default import ChatTypeFilter

private_router = Router()
private_router.message.filter(ChatTypeFilter(chat_types=["private"]))


@private_router.callback_query(F.data == "delete")
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()






