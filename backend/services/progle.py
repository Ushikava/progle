import logging
import secrets
from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, InvalidInputError
from core.words import is_known_word, load_words
from db.models import Game, User, Word
from models.progle import (
    GameState,
    GuessModel,
    GuessStatus,
    HintResponse,
    Hints,
    LeaderboardEntry,
    LetterHint,
    LetterResult,
)
from repositories.progle import GameRepo, WordRepo
from services.auth import avatar_url

LEADERBOARD_LIMIT = 50
REPEAT_COOLDOWN_DAYS = 365

logger = logging.getLogger(__name__)


def _today() -> date:
    return datetime.now(UTC).date()


def compare_words(target: str, guess: str) -> list[LetterResult]:
    statuses = [GuessStatus.ABSENT] * len(guess)
    remaining = Counter()

    for i, (g, t) in enumerate(zip(guess, target)):
        if g == t:
            statuses[i] = GuessStatus.CORRECT
        else:
            remaining[t] += 1

    for i, g in enumerate(guess):
        if statuses[i] != GuessStatus.CORRECT and remaining[g] > 0:
            statuses[i] = GuessStatus.PRESENT
            remaining[g] -= 1

    return [LetterResult(letter=g, status=s) for g, s in zip(guess, statuses)]


def _pick_candidates(pool: tuple[str, ...], last_used: dict[str, date], today: date) -> list[str]:
    cutoff = today - timedelta(days=REPEAT_COOLDOWN_DAYS)
    candidates = [w for w in pool if last_used.get(w, date.min) <= cutoff]
    if candidates:
        return candidates

    logger.warning(
        "Все %d слов выпадали за последние %d дней, повторяем самые давние",
        len(pool),
        REPEAT_COOLDOWN_DAYS,
    )
    oldest = min(last_used.get(w, date.min) for w in pool)
    return [w for w in pool if last_used.get(w, date.min) == oldest]


async def _get_today_word(session: AsyncSession) -> Word:
    words = WordRepo(session)
    today = _today()

    word = await words.get_by_date(today)
    if word is not None:
        return word

    chosen = secrets.choice(_pick_candidates(load_words(), await words.get_last_used_dates(), today))
    await words.create_if_missing(chosen, today, _pick_hint_positions(len(chosen)))
    await session.commit()

    return await words.get_by_date(today)


def _pick_hint_positions(length: int, first: int | None = None) -> tuple[int, int]:
    if first is None:
        first = secrets.randbelow(length)
    second = secrets.choice([i for i in range(length) if i != first])
    return first, second


async def _ensure_hint_positions(session: AsyncSession, word: Word) -> None:
    if word.hint_position is None or word.second_hint_position is None:
        first, second = _pick_hint_positions(len(word.word), word.hint_position)
        await WordRepo(session).set_hint_positions_if_missing(word.id, first, second)
        await session.commit()
        await session.refresh(word)


def _check_hint_allowed(game: Game, level: int) -> None:
    if game.solved:
        raise ConflictError("Слово уже отгадано")
    if level != game.hints_used + 1:
        raise ConflictError("Сначала возьмите предыдущую подсказку")


def _build_hints(word: Word, game: Game) -> Hints:
    target = word.word.lower()
    positions = [word.hint_position, word.second_hint_position][: game.hints_used]
    return Hints(
        used=game.hints_used,
        letters=[LetterHint(position=p, letter=target[p]) for p in positions if p is not None],
    )


async def get_word_length(session: AsyncSession) -> int:
    word = await _get_today_word(session)
    return len(word.word)


async def get_game_state(session: AsyncSession, user: User) -> GameState:
    word = await _get_today_word(session)
    game = await GameRepo(session).get_or_create(user.id, word.id)
    await session.commit()

    target = word.word.lower()
    return GameState(
        word_length=len(target),
        n_of_tries=game.attempts,
        solved=game.solved,
        guesses=[compare_words(target, g.word) for g in game.guesses],
        hints=_build_hints(word, game),
    )


async def take_hint(session: AsyncSession, user: User, level: int) -> HintResponse:
    word = await _get_today_word(session)
    await _ensure_hint_positions(session, word)

    games = GameRepo(session)
    game = await games.get_or_create(user.id, word.id, lock=True)
    if level > game.hints_used:
        _check_hint_allowed(game, level)
        game.hints_used = level
        game.attempts += 1
    await session.commit()

    return HintResponse(n_of_tries=game.attempts, hints=_build_hints(word, game))


async def make_guess(session: AsyncSession, user: User, word: str) -> GuessModel:
    word = word.strip().lower()
    today_word = await _get_today_word(session)
    target = today_word.word.lower()

    if not word.isalpha():
        raise InvalidInputError("Слово должно состоять только из букв")
    if len(word) != len(target):
        raise InvalidInputError(f"Слово должно состоять из {len(target)} букв")
    if not is_known_word(word):
        raise InvalidInputError("Такого слова нет в словаре")

    games = GameRepo(session)
    game = await games.get_or_create(user.id, today_word.id, lock=True)
    if game.solved:
        raise ConflictError("Слово уже отгадано")

    games.add_guess(game, word)
    game.attempts += 1
    if word == target:
        game.solved = True
        game.solved_at = datetime.now(UTC)

    await session.commit()

    return GuessModel(
        letters=compare_words(target, word),
        n_of_tries=game.attempts,
        solved=game.solved,
    )


async def get_leaderboard(session: AsyncSession) -> list[LeaderboardEntry]:
    word = await _get_today_word(session)
    rows = await GameRepo(session).get_leaderboard(word.id, LEADERBOARD_LIMIT)
    return [
        LeaderboardEntry(
            rank=rank,
            username=user.username,
            avatar_url=avatar_url(user),
            n_of_tries=game.attempts,
            hints_used=game.hints_used,
            solved_at=game.solved_at,
        )
        for rank, (game, user) in enumerate(rows, start=1)
    ]
