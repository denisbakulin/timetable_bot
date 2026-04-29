from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script: `py .\app\main.py` (adds project root to sys.path).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import logging

from aiogram import Bot, Dispatcher
from app.settings import bot_settings
from app.setup import setup
from aiogram.client.default import DefaultBotProperties

from app.fsm.default import storage


logging.basicConfig(level=logging.DEBUG)
bot = Bot(
    token=bot_settings.token,
    default=DefaultBotProperties(parse_mode='HTML'),
)

dp = Dispatcher(storage=storage)


async def main() -> None:

    await setup(dp, bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




