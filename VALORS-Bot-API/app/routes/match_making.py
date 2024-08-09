from fastapi import APIRouter, Request

from ..utils.database import get_match_making_leaderboard

router = APIRouter()

@router.get("/leaderboard")
async def leaderboard(request: Request):
    leaderboard = await get_match_making_leaderboard(request.state.db, 1217224187454685295)
    return leaderboard