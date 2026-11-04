from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GuessStatus(str, Enum):
    CORRECT = "correct"
    PRESENT = "present"
    ABSENT = "absent"


class LetterResult(BaseModel):
    letter: str
    status: GuessStatus


class GuessRequest(BaseModel):
    word: str = Field(min_length=1, max_length=32)


class GuessModel(BaseModel):
    letters: list[LetterResult]
    n_of_tries: int
    solved: bool


class LetterHint(BaseModel):
    position: int
    letter: str


class Hints(BaseModel):
    used: int
    letters: list[LetterHint]


class GameState(BaseModel):
    word_length: int
    n_of_tries: int
    solved: bool
    guesses: list[list[LetterResult]]
    hints: Hints


class HintResponse(BaseModel):
    n_of_tries: int
    hints: Hints


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    avatar_url: str
    n_of_tries: int
    hints_used: int
    solved_at: datetime
