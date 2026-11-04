from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def upsert(self, discord_id: str, username: str, avatar: str | None) -> User:
        query = (
            insert(User)
            .values(discord_id=discord_id, username=username, avatar=avatar)
            .on_conflict_do_update(
                index_elements=[User.discord_id],
                set_={"username": username, "avatar": avatar},
            )
            .returning(User)
        )
        return await self.session.scalar(query, execution_options={"populate_existing": True})

    async def revoke_tokens(self, user_id: int) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(token_version=User.token_version + 1)
        )
