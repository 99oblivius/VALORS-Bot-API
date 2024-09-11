import hmac
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..utils.pipe_utils import write_to_pipe_with_timeout
from ..utils.logger import log
from config import config

async def handle_update(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail={"error": "Missing Authorization header"})
    
    update_type = request.query_params.get('type', None)
    
    if update_type not in ['regular', 'force']:
        log.error(f"/update invalid")
        raise HTTPException(status_code=400, detail={"error": "Invalid update type"})

    if not hmac.compare_digest(auth_header, config.UPDATE_API_KEY):
        log.error(f"{update_type.upper()} UPDATE authentication failed")
        raise HTTPException(status_code=401, detail={"error": f"Invalid token for {update_type} update"})
    
    script = 'update.sh' if update_type == 'regular' else 'force_update.sh'
    if write_to_pipe_with_timeout('/hostpipe/apipipe', script):
        log.info(f"{update_type.upper()} UPDATE called successfully")
        log.info(f"sent by: {request.headers.get('x-forwarded-for', -1)}")
        return JSONResponse(content={'status': f'{update_type.capitalize()} Update initiated successfully'}, status_code=200)
    
    log.error(f"{update_type.upper()} UPDATE failed")
    raise HTTPException(status_code=500, detail={"error": f"Failed to initiate {update_type} update"})