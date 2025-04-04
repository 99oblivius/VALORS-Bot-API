from fastapi import APIRouter, Request, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional
from ..discord import get_client
from ..utils.database import (
    get_user_roles, 
    get_users_roles, 
    get_user_from_session, 
    get_user_from_discord, 
    add_user_role, 
    remove_user_role,
    Roles,
    get_users,
    total_user_count,
    get_user_team,
)
from ..services.login_session_manager import SessionManager
from ..utils.utils import verify_permissions

router = APIRouter()

@router.get("/")
async def user_info(
    request: Request,
    discord_user_id: int = Query(alias="id"),
    show_team: bool = Query(False, alias="team", description="Include team information"),
):
    user = await get_user_from_discord(request.state.db, discord_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    client = get_client()
    avatar = await client.get_avatar_url(request.app.redis_db, discord_user_id)

    roles = await get_user_roles(request.state.db, user.id)
    
    response_data = {
        "id": user.id,
        "discord_id": user.discord_id,
        "username": user.username,
        "avatar": avatar,
        "roles": [role.value for role in roles],
    }

    if show_team:
        team = await get_user_team(request.state.db, user.id)
        response_data["team"] = team

    token = request.headers.get('session-token', None)
    if token:
        user_session = await SessionManager.fetch(request.state.db, token)
        if not user_session:
            raise HTTPException(status_code=401, detail="Invalid session token")

        roles = await get_user_roles(request.state.db, user_session.user_id)
        if Roles.ADMIN in roles:
            response_data.update({
                "email": user.email,
                "is_active": user.is_active
            })

    return JSONResponse(status_code=200, content={'user': response_data})

@router.get("/me")
async def user_info(
    request: Request, 
    show_team: bool = Query(False, alias="team", description="Include team information")
):
    verify_permissions(request, Roles.USER)

    response_data = {}
    session_token = request.headers.get('session-token', None)

    user = await get_user_from_session(request.state.db, session_token)
    if show_team:
        team = await get_user_team(request.state.db, user.id)
        response_data["team"] = team
    
    if user:
        response_data.update({
            "id": user.id, 
            "discord_id": user.discord_id, 
            "username": user.username, 
            "email": user.email, 
            "roles": [role.value for role in await get_user_roles(request.state.db, user.id)],
            "is_active": user.is_active})
    return JSONResponse(status_code=200, content={'user': response_data})

@router.get("/all")
async def all_users(
    request: Request,
    search: str = Query(None, description="Search string for username"),
    last_username: Optional[str] = Query(None, description="Last username for pagination"),
    limit: int = Query(20, description="Number of results to return", ge=1, le=100)
):
    verify_permissions(request, Roles.ADMIN)

    if last_username in ('null', 'undefined', ''):
        last_username = None
    
    users = await get_users(
        request.state.db,
        search=search,
        last_username=last_username,
        limit=limit)
    
    total_users = await total_user_count(request.state.db)
    filtered_users_total = await total_user_count(request.state.db, search=search)
    
    if len(users) == 0:
        user = await get_user_from_discord(request.state.db, search)
        if user:
            users.append({
                "id": user.id,
                "discord_id": user.discord_id,
                "username": user.username
            })
            filtered_users_total = 1
    
    users_roles = await get_users_roles(request.state.db, [u['id'] for u in users])
    for user in users:
        user.pop('email')
        user.update({ 'roles': users_roles.get(user['id'], None) })
        
    last_username = users[-1]['username'] if users else None

    return JSONResponse(
        status_code=200,
        content={
            'users': users,
            'filtered_total': filtered_users_total,
            'total': total_users,
            'last_username': last_username,
        })

@router.get("/roles")
async def get_roles(request: Request):
    roles = list(sorted({role.value for role in Roles}))
    return JSONResponse(status_code=200, content={ 'roles': roles })

@router.post("/{discord_user_id}/roles/{role}")
async def add_role(
    request: Request,
    discord_user_id: int = Path(..., description="Discord user ID"),
    role: Roles = Path(..., description="Role to add")
):
    user = await get_user_from_discord(request.state.db, discord_user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    verify_permissions(request, Roles.ADMIN, notselfcheck=user.id)
    
    try:
        if not await add_user_role(request.state.db, user.id, role):
            raise Exception("User already has role")
        return JSONResponse(status_code=200, content={"message": f"Role {role.value} added to user {user.id}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": f"Failed to add role: {str(e)}"})

@router.delete("/{discord_user_id}/roles/{role}")
async def remove_role(
    request: Request,
    discord_user_id: int = Path(..., description="Discord user ID"),
    role: Roles = Path(..., description="Role to remove")
):
    user = await get_user_from_discord(request.state.db, discord_user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    verify_permissions(request, Roles.ADMIN, notselfcheck=user.id)
    
    try:
        if not await remove_user_role(request.state.db, user.id, role):
            raise Exception("User does not have role")
        return JSONResponse(status_code=200, content={"message": f"Role {role.value} removed from user {user.id}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": f"Failed to remove role: {str(e)}"})
