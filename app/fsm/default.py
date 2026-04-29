from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from app.settings import bot_settings

try:
    from aiogram.fsm.storage.redis import RedisStorage  # type: ignore
    from redis.asyncio.client import Redis  # type: ignore
except Exception:
    RedisStorage = None  # type: ignore
    Redis = None  # type: ignore


def _build_storage():
    if not bot_settings.fsm_redis_url:
        return MemoryStorage()

    if RedisStorage is None or Redis is None:
        return MemoryStorage()

    try:
        redis_client = Redis.from_url(bot_settings.fsm_redis_url)
        return RedisStorage(redis=redis_client)
    except Exception:
        return MemoryStorage()


storage = _build_storage()



class Waiting(StatesGroup):
    feedback = State()
    group = State()
    notify_time = State()

    dist = State()
    setup_group = State()
