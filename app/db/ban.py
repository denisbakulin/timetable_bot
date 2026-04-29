from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService


class Ban(BaseORM):
    __tablename__ = "bans"

    tg_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(default="", nullable=False)


class BanSchema(BaseSchema):
    tg_id: int
    reason: str


class BanRepository(BaseRepository[Ban]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Ban)


class BanService(BaseService[Ban, BanRepository, BanSchema]):
    model = Ban
    repository = BanRepository
    schema = BanSchema

    async def is_banned(self, tg_id: int) -> bool:
        row = await self.get_one_by(tg_id=tg_id)
        return row is not None

    async def unban(self, tg_id: int) -> bool:
        row = await self.get_one_by(tg_id=tg_id)
        if row is None:
            return False
        await self.delete(row.id)
        return True
