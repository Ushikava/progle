from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64))
    avatar: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    token_version: Mapped[int] = mapped_column(default=0, server_default="0")

    games: Mapped[list["Game"]] = relationship(back_populates="user")


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(32))
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    hint_position: Mapped[int | None]
    second_hint_position: Mapped[int | None]

    games: Mapped[list["Game"]] = relationship(back_populates="word")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (UniqueConstraint("user_id", "word_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    solved: Mapped[bool] = mapped_column(default=False, server_default="false")
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hints_used: Mapped[int] = mapped_column(default=0, server_default="0")

    user: Mapped["User"] = relationship(back_populates="games")
    word: Mapped["Word"] = relationship(back_populates="games")
    guesses: Mapped[list["Guess"]] = relationship(
        back_populates="game", order_by="Guess.id", cascade="all, delete-orphan"
    )


class Guess(Base):
    __tablename__ = "guesses"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"), index=True)
    word: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game: Mapped["Game"] = relationship(back_populates="guesses")
