from typing import Final

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote, Spoiler, Text

from app.filters.default import ChatTypeFilter, ReplyFeedbackMessage
from app.settings import bot_settings

router = Router()
router.message.filter(ChatTypeFilter(chat_types=["group", "supergroup"]))

ADMIN_ROLES: Final = {"administrator", "creator"}



async def init_admins(bot: Bot):
    admins = await bot.get_chat_administrators(bot_settings.admin_chat_id)
    admins_ids = [
        admin.user.id
        for admin in admins
        if admin.status in ADMIN_ROLES
    ]
    bot.admins = admins_ids


@router.message(Command("init"))
async def command_init_admins(message: Message, bot: Bot):
    """Обновляет список администраторов"""

    await init_admins(bot)
    await message.answer("ok")


@router.message(ReplyFeedbackMessage())
async def reply_to_feedback(message: Message, bot: Bot):
    """Ответить на обращение feedback"""

    chat_id = int(message.reply_to_message.text.split()[0])

    text = " ".join(message.reply_to_message.text.split()[1:])

    await message.reply_to_message.edit_text(
        f"{chat_id} {text}  ✅"
    )
    content = Text(f"Ответ на ваше обращение \n\n", Spoiler(text), "\n\n", BlockQuote(message.text))
    await bot.send_message(
        chat_id=chat_id,
        **content.as_kwargs()
    )


