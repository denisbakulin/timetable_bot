import logging

from aiogram import Bot, Dispatcher, types
from app.settings import bot_settings
from app.setup import setup
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI
from typing import Any

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=bot_settings.token, default=DefaultBotProperties(parse_mode='HTML'))

dp = Dispatcher()

app = FastAPI()

WEBHOOK_URL = "/webhook"
@app.on_event("startup")
async def startup():
    await setup(dp, bot)
    webhook_url = bot_settings.host + WEBHOOK_URL
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != webhook_url:
        await bot.set_webhook(
            url=webhook_url
        )


@app.post(WEBHOOK_URL)
async def webhook(update: dict[str, Any]):
    await dp.feed_webhook_update(bot=bot, update=types.Update(**update))


@app.on_event("shutdown")
async def shutdown():
    await bot.delete_webhook(drop_pending_updates=True)





