from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.data import ABOUT_TEXT
from app.keyboards.kb import about_kb

router = Router()

@router.message(Command("about"))
async def start(message: Message):

    await message.answer(
        ABOUT_TEXT,
        disable_web_page_preview=True,
        reply_markup=about_kb,
    )