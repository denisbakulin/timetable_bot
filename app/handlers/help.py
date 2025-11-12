from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.data import HELP_TEXT
from app.keyboards.kb import main_menu_kb

router = Router()

@router.message(Command("help"))
async def process_subscribe(message: Message):
    await message.answer(HELP_TEXT,  reply_markup=main_menu_kb)
