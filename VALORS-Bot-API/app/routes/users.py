from fastapi import APIRouter, Request, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional
from ..utils.database import (
    get_user_roles, 
    get_users_roles, 
    get_user_from_session, 
    get_user_from_discord, 
    add_user_role, 
    remove_user_role,
    Roles,
    fetch_users,
    total_user_count
)
from ..services.login_session_manager import SessionManager
from ..utils.utils import verify_permissions

router = APIRouter()

@router.get("/")
async def user_info(request: Request, discord_user_id: int = Query(alias="id")):
    verify_permissions(request, Roles.MOD, Roles.ADMIN)

    response_data = {}
    user = await get_user_from_discord(request.state.db, discord_user_id)
    if user:
        response_data.update({
            "id": user.id, 
            "discord_id": user.discord_id, 
            "username": user.username, 
            "email": user.email, 
            "roles": [role.value for role in await get_user_roles(request.state.db, user.id)],
            "is_active": user.is_active})
    return JSONResponse(status_code=200, content={'user': response_data})

@router.get("/me")
async def user_info(request: Request):
    verify_permissions(request, Roles.USER)

    response_data = {}
    session_token = request.headers.get('session-token', None)
    user = await get_user_from_session(request.state.db, session_token)
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

    session_token = request.headers.get('session-token', None)
    if not session_token:
        raise HTTPException(status_code=401, detail={"error": "Missing User Session token"})

    session = await SessionManager.fetch(request.state.db, session_token)
    if not session:
        raise HTTPException(status_code=401, detail={"error": "Invalid User Session token"})
    current_user = await get_user_from_session(request.state.db, session_token)
    user_roles = await get_user_roles(request.state.db, current_user.id)
    if Roles.ADMIN not in user_roles and Roles.MOD not in user_roles:
        raise HTTPException(status_code=403, detail={"error": "Insufficient permissions"})

    if last_username in ('null', 'undefined', ''):
        last_username = None
    
    users = await fetch_users(
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
    
    users_roles = await get_users_roles(request.state.db, [u['id'] for u in users])
    for user in users:
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