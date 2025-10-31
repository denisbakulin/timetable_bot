from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.data import MENU_TEXT
from app.db.base import UserService
from app.keyboards.kb import menu_kb
from aiogram.fsm.context import FSMContext

router = Router()


async def create_menu_message(message: Message, user_id: int, edit=False):
    user = await UserService().get_user_by_tg_id(user_id)
    text = MENU_TEXT.format(group=user.group)

    func = message.edit_text if edit else message.answer

    await func(text, reply_markup=menu_kb, parse_mode="HTML")


@router.message(Command("menu"))
@router.message(F.text == "Меню")
async def get_me(message: Message, state: FSMContext):
    await create_menu_message(message, message.from_user.id)
    await state.clear()


@router.callback_query(F.data == "menu")
async def get_me(callback: CallbackQuery):
    await create_menu_message(callback.message, callback.from_user.id, edit=True)



