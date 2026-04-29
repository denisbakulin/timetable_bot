from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.db.ban import BanService


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        # Allow admins to operate even if they accidentally banned themselves.
        bot = data.get("bot")
        if bot is not None and getattr(bot, "admins", None) and user.id in bot.admins:
            return await handler(event, data)

        if await BanService().is_banned(user.id):
            # Silent drop.
            if isinstance(event, CallbackQuery):
                try:
                    await event.answer("Доступ ограничен.", show_alert=True)
                except Exception:
                    pass
            elif isinstance(event, Message):
                try:
                    await event.answer("Доступ ограничен.")
                except Exception:
                    pass
            return None

        return await handler(event, data)

