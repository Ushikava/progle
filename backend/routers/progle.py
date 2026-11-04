from typing import Annotated

from fastapi import APIRouter, Path

from models.progle import (
    GameState,
    GuessModel,
    GuessRequest,
    HintResponse,
    LeaderboardEntry,
)
from routers.dependencies import CurrentUser, SessionDep
from services.progle import (
    get_game_state,
    get_leaderboard,
    get_word_length,
    make_guess,
    take_hint,
)

router = APIRouter(prefix="/progle", tags=["progle"])


@router.get("/word_length", response_model=int)
async def word_length(session: SessionDep):
    return await get_word_length(session)


@router.get("/game", response_model=GameState)
async def game(user: CurrentUser, session: SessionDep):
    return await get_game_state(session, user)


@router.post("/guess", response_model=GuessModel)
async def guess(body: GuessRequest, user: CurrentUser, session: SessionDep):
    return await make_guess(session, user, body.word)


@router.post("/hints/{level}", response_model=HintResponse)
async def hint(level: Annotated[int, Path(ge=1, le=2)], user: CurrentUser, session: SessionDep):
    return await take_hint(session, user, level)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(session: SessionDep):
    return await get_leaderboard(session)
