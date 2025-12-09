from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.data import MENU_TEXT
from app.db.user import UserService

from app.keyboards.kb import menu_kb

router = Router()


async def create_menu_message(message: Message, user_id: int, edit=False):
    user = await UserService().get_user_by_tg_id(user_id)
    group = user.group.name if user.group else None
    text = MENU_TEXT.format(group=group)

    func = message.edit_text if edit else message.answer

    await func(text, reply_markup=menu_kb)


@router.message(Command("menu"))
@router.message(F.text.lower() == "меню")
async def get_me(message: Message, state: FSMContext):
    await state.clear()
    await create_menu_message(message, message.from_user.id)



@router.callback_query(F.data == "menu")
async def get_menu_callback(callback: CallbackQuery):
    await create_menu_message(callback.message, callback.from_user.id, edit=True)


