from pathlib import Path
from pydantic_settings import BaseSettings


env_path = Path(__file__).parent.parent


class BotSettings(BaseSettings):
    token: str

    admin_chat_id: int
    feedback_thread_id: int

    timetable_url: str
    timetable_update_time_seconds: int

    cache_url: str
    cache_port: int

    class Config:
        env_file = env_path / ".env"


bot_settings = BotSettings()
