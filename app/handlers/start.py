from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.data import START_TEXT
from app.keyboards.kb import  main_menu_kb

router = Router()



@router.message(CommandStart())
async def start(message: Message):

    await message.answer(
        START_TEXT,
        reply_markup=main_menu_kb,
        parse_mode="HTML"
    )
