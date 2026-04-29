from pathlib import Path
from pydantic_settings import BaseSettings


env_path = Path(__file__).parent.parent


class BotSettings(BaseSettings):
    token: str

    admin_chat_id: int
    feedback_thread_id: int

    timetable_url: str
    # Proxy for requests to timetable.pallada.sibsau.ru when running outside РФ.
    # Example: http://user:pass@host:port
    timetable_proxy: str | None = None
    timetable_update_time_seconds: int

    # Optional Redis for cache (timetable HTML/JSON snapshots).
    cache_url: str | None = None
    cache_port: int | None = None

    # Optional Redis for aiogram FSM storage.
    # If not set or Redis is unavailable, the bot falls back to in-memory storage.
    fsm_redis_url: str | None = None

    class Config:
        env_file = env_path / ".env"


bot_settings = BotSettings()
