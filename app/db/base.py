from sqlalchemy import select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, with_parent

engine = create_async_engine(url="sqlite+aiosqlite:///bot.db")
session_maker = async_sessionmaker(bind=engine)
from datetime import time
from typing import TypeVar, Generic, AsyncGenerator
from contextlib import asynccontextmanager
from pydantic import BaseModel, ConfigDict
from app.settings import bot_settings
class BaseSchema(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserSchema(BaseSchema):
    tg_id: int
    subscribe: bool
    group: str | None
    notify_time: time

class GroupSchema(BaseSchema):
    pallada_id: int
    name: str

    def __str__(self):
        return f"<a href='{bot_settings.timetable_url}/group/{self.pallada_id}'>{self.name}</a>"


S = TypeVar("S", bound=BaseSchema)

class BaseORM(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)



class User(BaseORM):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    subscribe: Mapped[bool] = mapped_column(default=True)
    group: Mapped[str | None]
    notify_time: Mapped[time] = mapped_column(default=time(hour=7, minute=0))


    def __repr__(self):
        return f"Пользователь [Рассылка: {self.subscribe}, Группа: {self.group}]"

class Group(BaseORM):
    __tablename__ = "groups"

    name: Mapped[str]
    pallada_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)



M = TypeVar("M", bound=BaseORM)

class BaseRepository(Generic[M]):

    def __init__(self, session: AsyncSession, model: type[M]):
        self.session = session
        self.model = model

    async def get_one_by(self, **params) -> M | None:
        stmt = select(self.model).filter_by(**params)

        item = await self.session.execute(stmt)
        return item.scalars().one_or_none()

    async def get_any_by(self, **params) -> list[M]:
        stmt = select(self.model).filter_by(**params)

        item = await self.session.execute(stmt)

        return [*item.scalars().all()]

    async def save(self, item: M) -> M:
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def create(self, **data) -> M:
        item = self.model(**data)
        self.session.add(item)
        return await self.save(item)

    async def update(self, item: M, **fields) -> M:
        for key, value in fields.items():
            setattr(item, key, value)
        return await self.save(item)


class GroupRepository(BaseRepository[Group]):
    primary_key = "pallada_id"

    def __init__(self, session: AsyncSession):
        super().__init__(session, Group)


class UserRepository(BaseRepository[User]):
    primary_key = "tg_id"

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)


R = TypeVar("R", bound=BaseRepository)


class BaseService(Generic[M, R, S]):

    model: type[M]
    repository: type[R]
    schema: type[S]


    def serialize(self, item: M) -> S:
        return self.schema.from_orm(item)

    @asynccontextmanager
    async def with_repo(self) -> AsyncGenerator[BaseRepository[M], None]:
        async with session_maker() as session:
            repo = self.repository(session)
            try:
                yield repo
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()

    async def get_any_by(self, **params) -> list[S]:
        async with self.with_repo() as repo:
            items = await repo.get_any_by(**params)
            return [self.serialize(item) for item in items]

    async def get_one_by(self, **params) -> S | None:
        async with self.with_repo() as repo:
            item = await repo.get_one_by(**params)
            return self.serialize(item) if item else None

    async def create(self, **params) -> S:
        async with self.with_repo() as repo:
            item = await repo.create(**params)
            return self.serialize(item)

    async def update(self, item_id: int, **updates) -> S:
        async with self.with_repo() as repo:
            item = await repo.get_one_by(id=item_id)
            updated_item = await repo.update(item, **updates)
            return self.serialize(updated_item)


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


class GroupService(BaseService[Group, GroupRepository, GroupSchema]):
    model = Group
    repository = GroupRepository
    schema = GroupSchema




async def init_db():
    async with engine.connect() as conn:
        await conn.run_sync(BaseORM.metadata.create_all)