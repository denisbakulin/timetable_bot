from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService


class GroupRefresh(BaseORM):
    __tablename__ = "group_refresh"

    pallada_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    last_refresh_ts: Mapped[int | None]
    last_ok: Mapped[bool] = mapped_column(default=False)
    last_error: Mapped[str] = mapped_column(default="", nullable=False)


class GroupRefreshSchema(BaseSchema):
    pallada_id: int
    last_refresh_ts: int | None
    last_ok: bool
    last_error: str

    def format_when(self) -> str:
        if not self.last_refresh_ts:
            return "never"
        return datetime.fromtimestamp(self.last_refresh_ts).isoformat(sep=" ", timespec="seconds")


class GroupRefreshRepository(BaseRepository[GroupRefresh]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupRefresh)


class GroupRefreshService(BaseService[GroupRefresh, GroupRefreshRepository, GroupRefreshSchema]):
    model = GroupRefresh
    repository = GroupRefreshRepository
    schema = GroupRefreshSchema

    async def mark(self, pallada_id: int, *, ok: bool, error: str = "") -> GroupRefreshSchema:
        row = await self.get_one_by(pallada_id=pallada_id)
        now_ts = int(datetime.now().timestamp())
        if row is None:
            return await self.create(
                pallada_id=pallada_id,
                last_refresh_ts=now_ts,
                last_ok=ok,
                last_error=error[:400],
            )
        return await self.update(
            row.id,
            last_refresh_ts=now_ts,
            last_ok=ok,
            last_error=(error[:400] if not ok else ""),
        )

