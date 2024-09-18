from fastapi import APIRouter, Request, HTTPException, Query, Path, Body, File, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional, List
from ..utils.database import (
    get_team,
    update_team,
    fetch_teams,
    total_team_count,
    Roles,
    join_request,
    get_team_join_requests,
    process_join_request,
    is_team_captain,
    is_team_co_captain,
    is_user_in_team,
    get_user_from_session,
    remove_team_member,
    get_team_members,
    get_active_teams,
    create_team,
    total_team_count,
    disband_team
)
from ..utils.utils import verify_permissions

router = APIRouter()

@router.get("/")
async def team_info(request: Request, team_id: int = Query(alias="id")):
    response_data = {}
    team = await get_team(request.state.db, team_id)
    if team:
        response_data.update({
            "id": team.id,
            "name": team.name,
            "bio": team.bio,
            "color1": team.color1,
            "color2": team.color2,
            "logo_url": team.logo_url,
            "display_trophy": team.display_trophy,
            "timestamp": team.timestamp.isoformat(),
            "disbanded_at": team.disbanded_at
        })
    return JSONResponse(status_code=200, content={'team': response_data})

@router.put("/update")
async def update_info(
    request: Request,
    team_id: int = Query(..., alias="id"),
    team_data: dict = Body(...),
    logo_file: UploadFile = File(None)
):
    try:
        updated_team = await update_team(request.state.db, team_id, team_data, logo_file)
        if updated_team:
            return JSONResponse(status_code=200, content={'message': 'Team updated successfully', 'team': updated_team})
        else:
            raise HTTPException(status_code=404, detail="Team not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update team: {str(e)}")

@router.get("/all")
async def all_teams(
    request: Request,
    search: str = Query(None, description="Search string for team name"),
    last_team_name: Optional[str] = Query(None, description="Last team name for pagination"),
    limit: int = Query(20, description="Number of results to return", ge=1, le=100)
):
    if last_team_name in ('null', 'undefined', ''):
        last_team_name = None
    
    teams = await fetch_teams(
        request.state.db,
        search=search,
        last_team_name=last_team_name,
        limit=limit
    )
    
    total_teams = await total_team_count(request.state.db)
    filtered_teams_total = await total_team_count(request.state.db, search=search)
    
    team_list = [{
        "id": team.id,
        "name": team.name,
        "bio": team.bio,
        "color1": team.color1,
        "color2": team.color2,
        "logo_url": team.logo_url,
        "display_trophy": team.display_trophy,
        "timestamp": team.timestamp.isoformat(),
        "disbanded_at": team.disbanded_at
    } for team in teams]
        
    last_team_name = team_list[-1]['name'] if team_list else None

    return JSONResponse(
        status_code=200,
        content={
            'teams': team_list,
            'filtered_total': filtered_teams_total,
            'total': total_teams,
            'last_team_name': last_team_name,
        })

@router.get("/{team_id}/members")
async def get_members(
    request: Request,
    team_id: int = Path(..., description="Team ID"),
):
    team = await get_team(request.state.db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    members = await get_team_members(request.state.db, team_id)
    return JSONResponse(status_code=200, content={'members': members})

@router.post("/join-request")
async def create_join_request(
    request: Request,
    team_id: int = Query(..., description="ID of the team to join")
):
    if await is_user_in_team(request.state.db, request.state.user_id):
        raise HTTPException(status_code=403, detail="You cannot request as long as you are in a team")
    
    request = await join_request(request.state.db, team_id, request.state.user_id)
    return JSONResponse(status_code=200, content={'message': 'Join request created successfully', 'request_id': request.id})

@router.get("/{team_id}/join-requests")
async def list_join_requests(
    request: Request,
    team_id: int = Path(..., description="ID of the team")
):
    if not (
        await is_team_captain(request.state.db, team_id, request.state.user_id) 
        or await is_team_co_captain(request.state.db, team_id, request.state.user_id)):
        raise HTTPException(status_code=403, detail="You must be a team captain or co-captain to view join requests")
    
    join_requests = await get_team_join_requests(request.state.db, team_id)
    return JSONResponse(status_code=200, content={'join_requests': [{'id': jr.id, 'user_id': jr.user_id, 'timestamp': jr.timestamp.isoformat()} for jr in join_requests]})

@router.post("/join-request/{request_id}/process")
async def process_join(
    request: Request,
    request_id: int = Path(..., description="ID of the join request"),
    accept: bool = Query(..., description="Whether to accept or decline the request")
):
    join_request = await process_join_request(request.state.db, request_id, accept)
    
    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")
    
    if not await is_team_captain(request.state.db, join_request.team_id, request.state.user_id):
        raise HTTPException(status_code=403, detail="You must be a team captain to process join requests")
    
    action = "accepted" if accept else "declined"
    return JSONResponse(status_code=200, content={'message': f'Join request {action} successfully'})

@router.post("/{team_id}/kick/{user_id}")
async def kick_user(
    request: Request,
    team_id: int = Path(..., description="ID of the team"),
    user_id: int = Path(..., description="ID of the user to kick")
):
    is_captain = await is_team_captain(request.state.db, team_id, request.state.user_id)
    
    if not (is_captain):
        raise HTTPException(status_code=403, detail="You must be a team captain to kick users")
    
    user_to_kick_is_captain = await is_team_captain(request.state.db, team_id, user_id)
    
    if user_to_kick_is_captain:
        raise HTTPException(status_code=403, detail="Cannot kick a team captain")
    
    success = await remove_team_member(request.state.db, team_id, user_id)
    
    if success:
        return JSONResponse(status_code=200, content={'message': 'User successfully kicked from the team'})
    else:
        raise HTTPException(status_code=404, detail="User not found in the team or already left")

@router.post("/create")
async def create_new(
    request: Request,
    team_data: dict = Body(..., description="Team data including name, bio, colors, etc.")
):
    verify_permissions(request, Roles.USER)
    
    if await is_user_in_team(request.state.db, request.state.user_id):
        raise HTTPException(status_code=401, detail="A team member cannot create a team")
    
    if 'name' not in team_data:
        raise HTTPException(status_code=401, detail="A team must have a name")

    new_team = await create_team(request.state.db, team_data, request.state.user_id)
    return JSONResponse(status_code=201, content={'team': {
        'id': new_team.id,
        'name': new_team.name,
        'timestamp': new_team.timestamp.isoformat()
    }})

@router.delete("/{team_id}")
async def disband_existing_team(
    request: Request,
    team_id: int = Path(..., description="Team ID to disband")
):
    verify_permissions(request, Roles.USER)
    
    if not await is_team_captain(request.state.db, team_id, request.state.user_id):
        raise HTTPException(status_code=403, detail="Only team captains can disband a team")
    
    if await disband_team(request.state.db, team_id):
        return JSONResponse(status_code=200, content={'message': 'Team successfully disbanded'})
    else:
        raise HTTPException(status_code=404, detail="Team not found or already disbanded")

@router.get("/all")
async def list_active_teams(
    request: Request,
    search: str = Query(None, description="Search string for team name"),
    last_team_name: Optional[str] = Query(None, description="Last team name for pagination"),
    limit: int = Query(20, description="Number of results to return", ge=1, le=100)
):
    verify_permissions(request, Roles.USER)

    if last_team_name in ('null', 'undefined', ''):
        last_team_name = None
    
    teams = await get_active_teams(
        request.state.db,
        search=search,
        last_team_name=last_team_name,
        limit=limit)
    
    total_teams = await total_team_count(request.state.db)
    filtered_teams_total = await total_team_count(request.state.db, search=search)
    
    teams_data = [{
        'id': team.id,
        'name': team.name,
        'logo_url': team.logo_url,
        'timestamp': team.timestamp.isoformat()
    } for team in teams]
        
    last_team_name = teams[-1].name if teams else None

    return JSONResponse(
        status_code=200,
        content={
            'teams': teams_data,
            'filtered_total': filtered_teams_total,
            'total': total_teams,
            'last_team_name': last_team_name,
        })