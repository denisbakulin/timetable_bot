from logging import getLogger

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

l = getLogger()

class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in bot.admins


class AnswerCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery, *args, **kwargs):
        await callback.answer()
        return True



class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_types: list[str]):
        self.chat_types = chat_types

    async def __call__(self, message: Message):
        return message.chat.type in self.chat_types


class ReplyFeedbackMessage(BaseFilter):
    async def __call__(self, m: Message, bot: Bot):
        flag = m.reply_to_message and m.reply_to_message.from_user.id == bot.id
        l.info(flag)
        if not flag:
            return False

        parse = m.reply_to_message.text.split()

        if len(parse) < 2:
            return False

        return parse[0].isdigit()

