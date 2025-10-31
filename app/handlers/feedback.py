from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.data import FEEDBACK_TEXT
from app.fsm.default import Waiting
from app.keyboards.kb import cancel_kb
from app.settings import bot_settings

router = Router()

@router.message(Command("feedback"))
async def feedback(message: Message, state: FSMContext):
    await message.answer(
        FEEDBACK_TEXT,
        reply_markup=cancel_kb)

    await state.set_state(Waiting.feedback)


@router.message(StateFilter(Waiting.feedback))
async def feedback_process_state(message: Message, state: FSMContext, bot: Bot):
    await bot.send_message(
        chat_id=bot_settings.admin_chat_id,
        text=f"{message.chat.id} {message.text}",
        message_thread_id=bot_settings.feedback_thread_id
    )
    await message.reply("Ваше сообщение успешно отправлено! Ожидайте ответа!")
    await state.clear()
