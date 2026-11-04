from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Game, Guess, User, Word


class WordRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_date(self, day: date) -> Word | None:
        query = select(Word).where(Word.date == day)
        return await self.session.scalar(query)

    async def get_last_used_dates(self) -> dict[str, date]:
        query = select(Word.word, func.max(Word.date)).group_by(Word.word)
        result = await self.session.execute(query)
        return {word: last_used for word, last_used in result}

    async def create_if_missing(self, word: str, day: date, hint_positions: tuple[int, int]) -> None:
        first, second = hint_positions
        await self.session.execute(
            insert(Word)
            .values(word=word, date=day, hint_position=first, second_hint_position=second)
            .on_conflict_do_nothing(index_elements=[Word.date])
        )

    async def set_hint_positions_if_missing(self, word_id: int, first: int, second: int) -> None:
        await self.session.execute(
            update(Word)
            .where(Word.id == word_id)
            .values(
                hint_position=func.coalesce(Word.hint_position, first),
                second_hint_position=func.coalesce(Word.second_hint_position, second),
            )
        )


class GameRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, word_id: int, lock: bool = False) -> Game:
        await self.session.execute(
            insert(Game)
            .values(user_id=user_id, word_id=word_id)
            .on_conflict_do_nothing(index_elements=[Game.user_id, Game.word_id])
        )

        query = (
            select(Game)
            .where(Game.user_id == user_id, Game.word_id == word_id)
            .options(selectinload(Game.guesses))
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    def add_guess(self, game: Game, word: str) -> Guess:
        guess = Guess(word=word)
        game.guesses.append(guess)
        return guess

    async def get_leaderboard(self, word_id: int, limit: int) -> list[tuple[Game, User]]:
        query = (
            select(Game, User)
            .join(User, Game.user_id == User.id)
            .where(Game.word_id == word_id, Game.solved)
            .order_by(Game.attempts, Game.solved_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.tuples())
