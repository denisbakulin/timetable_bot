from sqlalchemy import ForeignKey, UniqueConstraint, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, joinedload, mapped_column, relationship

from app.db.base import BaseORM, BaseRepository, BaseSchema, BaseService
from app.db.group import Group, GroupSchema


class UserFavoriteGroup(BaseORM):
    __tablename__ = "user_favorite_groups"
    __table_args__ = (
        UniqueConstraint("user_id", "group_pallada_id", name="uq_user_favorite_group"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_pallada_id: Mapped[int] = mapped_column(ForeignKey("groups.pallada_id"), index=True)
    group: Mapped[Group] = relationship("Group", lazy="joined")


class FavoriteGroupSchema(BaseSchema):
    user_id: int
    group_pallada_id: int
    group: GroupSchema


class FavoriteGroupRepository(BaseRepository[UserFavoriteGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserFavoriteGroup)

    async def get_user_favorites(self, user_id: int) -> list[UserFavoriteGroup]:
        stmt = (
            select(UserFavoriteGroup)
            .options(joinedload(UserFavoriteGroup.group))
            .where(UserFavoriteGroup.user_id == user_id)
            .order_by(UserFavoriteGroup.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class FavoriteGroupService(
    BaseService[UserFavoriteGroup, FavoriteGroupRepository, FavoriteGroupSchema]
):
    model = UserFavoriteGroup
    repository = FavoriteGroupRepository
    schema = FavoriteGroupSchema

    async def list_for_user(self, user_id: int) -> list[FavoriteGroupSchema]:
        async with self.with_repo() as repo:
            items = await repo.get_user_favorites(user_id)
            return [self.serialize(item) for item in items]

    async def add_for_user(self, user_id: int, group_pallada_id: int) -> FavoriteGroupSchema | None:
        async with self.with_repo() as repo:
            item = await repo.get_one_by(user_id=user_id, group_pallada_id=group_pallada_id)
            if item is not None:
                return self.serialize(item)

            created = await repo.create(user_id=user_id, group_pallada_id=group_pallada_id)
            item = await repo.get_one_by(id=created.id)
            return self.serialize(item) if item else None

    async def remove_for_user(self, user_id: int, group_pallada_id: int) -> bool:
        async with self.with_repo() as repo:
            item = await repo.get_one_by(user_id=user_id, group_pallada_id=group_pallada_id)
            if item is None:
                return False
            await repo.delete(item)
            return True
