from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService
from app.settings import bot_settings


class Group(BaseORM):
    __tablename__ = "groups"

    name: Mapped[str]
    pallada_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    timetable: Mapped[str | None]


class GroupSchema(BaseSchema):
    pallada_id: int
    name: str
    timetable: str | None

    def __str__(self):
        return f"<a href='{bot_settings.timetable_url}/group/{self.pallada_id}'>{self.name}</a>"


class GroupRepository(BaseRepository[Group]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, Group)

class GroupService(BaseService[Group, GroupRepository, GroupSchema]):
    model = Group
    repository = GroupRepository
    schema = GroupSchema


