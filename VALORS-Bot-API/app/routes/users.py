from fastapi import APIRouter, Request, HTTPException, Query, Depends, Path
from fastapi.responses import JSONResponse
from ..utils.database import (
    get_user_roles, 
    get_user_from_session, 
    get_user_from_discord, 
    add_role, 
    remove_role,
    Roles
)
from ..utils.utils import verify_auth
from sqlalchemy.ext.asyncio import AsyncSession
from config import config
from ..services.login_session_manager import SessionManager

router = APIRouter()

@router.get("/me")
async def user_info(request: Request, discord_user_id: int = Query(None, alias="user")):
    verify_auth(request, config.API_TOKEN)

    session_token = request.headers.get('session-token', None)
    session = await SessionManager.fetch(request.state.db, session_token)
    if session_token:
        if not session:
            raise HTTPException(status_code=401, detail={"error": "Invalid session token"})
        user = await get_user_from_session(request.state.db, session_token)
    else:
        user = await get_user_from_discord(request.state.db, discord_user_id)
    
    response_data = {
        "id": user.id, 
        "discord_id": user.discord_id, 
        "username": user.username, 
        "email": user.email, 
        "roles": [role.value for role in await get_user_roles(request.state.db, user.id)],
        "is_active": user.is_active
    }
    return JSONResponse(status_code=200, content={'user': response_data})

@router.post("/{discord_user_id}/roles/{role}")
async def add_user_role(
    request: Request,
    discord_user_id: int = Path(..., description="Discord user ID"),
    role: Roles = Path(..., description="Role to add")
):
    verify_auth(request, config.API_TOKEN)

    session_token = request.headers.get('session-token', None)
    session = await SessionManager.fetch(request.state.db, session_token)
    if session_token:
        if not session:
            raise HTTPException(status_code=401, detail={"error": "Invalid session token"})
        user = await get_user_from_session(request.state.db, session_token)
    
    user = await get_user_from_discord(request.state.db, discord_user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    
    try:
        await add_role(request.state.db, user.id, role)
        return JSONResponse(status_code=200, content={"message": f"Role {role.value} added to user {user.id}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": f"Failed to add role: {str(e)}"})

@router.delete("/{discord_user_id}/roles/{role}")
async def remove_user_role(
    request: Request,
    discord_user_id: int = Path(..., description="Discord user ID"),
    role: Roles = Path(..., description="Role to remove")
):
    verify_auth(request, config.API_TOKEN)

    user = await get_user_from_discord(request.state.db, discord_user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    
    await remove_role(request.state.db, user.id, role)
    try:
        return JSONResponse(status_code=200, content={"message": f"Role {role.value} removed from user {user.id}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": f"Failed to remove role: {str(e)}"})