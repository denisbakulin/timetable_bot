from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.group import Group, GroupSchema

from datetime import time
from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService



class User(BaseORM):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    subscribe: Mapped[bool] = mapped_column(default=False)
    notify_time: Mapped[time] = mapped_column(default=time(hour=7, minute=0))
    lesson_notify_minutes: Mapped[int] = mapped_column(default=0)
    last_lesson_notification_key: Mapped[str | None] = mapped_column(default=None)

    pallada_id: Mapped[int | None] = mapped_column(ForeignKey("groups.pallada_id"))
    group: Mapped[Group | None] = relationship("Group", lazy="joined")
    subgroup: Mapped[int] = mapped_column(default=0)

    def __repr__(self):
        return f"Пользователь [Рассылка: {self.subscribe}, Группа: {self.group}]"

class UserSchema(BaseSchema):
    tg_id: int
    subscribe: bool
    group: GroupSchema | None
    notify_time: time
    lesson_notify_minutes: int
    last_lesson_notification_key: str | None = None
    subgroup: int

class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_user_groups(self):

        stmt = (
            select(Group.name, func.count(User.group))
            .join(User, User.pallada_id == Group.pallada_id)
            .group_by(Group.id)
        )

        res = await self.session.execute(stmt)
        return res.tuples().all()


class UserService(BaseService[User, UserRepository, UserSchema]):
    model = User
    repository = UserRepository
    schema = UserSchema


    async def get_user_by_tg_id(self, tg_id: int) -> UserSchema:
        async with self.with_repo() as repo:
            user = await repo.get_one_by(tg_id=tg_id)
            if user is None:
                user = await repo.create(tg_id=tg_id, subscribe=False)

            return self.serialize(user)

    async def process_subscribe(self, tg_id: int) -> UserSchema:
        async with self.with_repo() as repo:
            user = await repo.get_one_by(tg_id=tg_id)
            updated_user = await repo.update(user, subscribe=not user.subscribe)
            return self.serialize(updated_user)

    async def set_group(self, tg_id: int, group: GroupSchema) -> UserSchema:
        async with self.with_repo() as repo:
            user = await repo.get_one_by(tg_id=tg_id)
            if user is None:
                user = await repo.create(tg_id=tg_id)
            user_id = user.id
            await repo.update(user, pallada_id=group.pallada_id)

        from app.db.favorite_group import FavoriteGroupService

        await FavoriteGroupService().add_for_user(user_id, group.pallada_id)
        return await self.get_user_by_tg_id(tg_id)


    async def get_all_ids(self) -> list[int]:
        users = await self.get_any_by()
        return [user.tg_id for user in users]

    async def get_user_groups(self) -> tuple[Group, int]:
        async with self.with_repo() as repo:
            return await repo.get_user_groups()

