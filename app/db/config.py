from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService


class AppConfig(BaseORM):
    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(nullable=False)


class AppConfigSchema(BaseSchema):
    key: str
    value: str


class AppConfigRepository(BaseRepository[AppConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AppConfig)


class AppConfigService(BaseService[AppConfig, AppConfigRepository, AppConfigSchema]):
    model = AppConfig
    repository = AppConfigRepository
    schema = AppConfigSchema

    async def get_value(self, key: str) -> str | None:
        row = await self.get_one_by(key=key)
        if not row or not row.value:
            return None
        return row.value

    async def set_value(self, key: str, value: str) -> AppConfigSchema:
        existing = await self.get_one_by(key=key)
        if existing is None:
            return await self.create(key=key, value=value)
        return await self.update(existing.id, value=value)

    async def delete_key(self, key: str) -> None:
        # Minimal implementation: set empty string is treated as "not set".
        # (Keeps repository simple; no delete method in BaseRepository.)
        await self.set_value(key, "")
