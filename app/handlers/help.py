from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.keyboards.kb import main_menu_kb

from app.data import HELP_TEXT

router = Router()

@router.message(Command("help"))
async def process_subscribe(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=main_menu_kb)
