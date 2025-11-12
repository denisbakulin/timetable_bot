from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.group import GroupSchema, Group
from datetime import time
from app.db.base import BaseORM, BaseSchema, BaseRepository, BaseService



class User(BaseORM):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    subscribe: Mapped[bool] = mapped_column(default=True)

    notify_time: Mapped[time] = mapped_column(default=time(hour=7, minute=0))

    pallada_id: Mapped[int | None] = mapped_column(ForeignKey("groups.pallada_id"))
    group: Mapped[str] = relationship("Group", lazy="joined")

    def __repr__(self):
        return f"Пользователь [Рассылка: {self.subscribe}, Группа: {self.group}]"

class UserSchema(BaseSchema):
    tg_id: int
    subscribe: bool
    group: GroupSchema | None
    notify_time: time

class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_user_groups(self):
        stmt = (
            select(Group.name)
            .join(User, User.pallada_id == Group.pallada_id)
            .distinct()
        )

        res = await self.session.execute(stmt)
        return res.scalars().all()

class UserService(BaseService[User, UserRepository, UserSchema]):
    model = User
    repository = UserRepository
    schema = UserSchema


    async def get_user_by_tg_id(self, tg_id: int) -> UserSchema:
        async with self.with_repo() as repo:
            user = await repo.get_one_by(tg_id=tg_id)
            if user is None:
                user = await repo.create(tg_id=tg_id)

            return self.serialize(user)

    async def process_subscribe(self, tg_id: int) -> UserSchema:
        async with self.with_repo() as repo:
            user = await repo.get_one_by(tg_id=tg_id)
            updated_user = await repo.update(user, subscribe=not user.subscribe)
            return self.serialize(updated_user)


    async def get_all_ids(self) -> list[int]:
        users = await self.get_any_by()
        return [user.tg_id for user in users]

    async def get_user_groups(self) -> list[str]:
        async with self.with_repo() as repo:
            res = await repo.get_user_groups()
            return [*res]



