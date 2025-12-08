import asyncio
import logging

from aiogram import Bot, Dispatcher
from app.settings import bot_settings
from app.setup import setup
from aiogram.client.default import DefaultBotProperties


logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=bot_settings.token, default=DefaultBotProperties(parse_mode='HTML'))

dp = Dispatcher()


async def main() -> None:

    await setup(dp, bot)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())




