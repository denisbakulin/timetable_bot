from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


from contextlib import asynccontextmanager

from typing import AsyncGenerator, Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pathlib import Path

# Создаем папку data если её нет
data_dir = Path(__file__).parent.parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Путь к базе данных в папке data
DB_PATH = data_dir / "bot.db"


engine = create_async_engine(
    url=f"sqlite+aiosqlite:///{DB_PATH}",
    echo=True  # для отладки SQL запросов
)

session_maker = async_sessionmaker(bind=engine)


class BaseSchema(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)



S = TypeVar("S", bound=BaseSchema)

class BaseORM(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


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


async def init_db():
    async with engine.connect() as conn:
        await conn.run_sync(BaseORM.metadata.create_all)