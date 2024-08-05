import hmac
from flask import jsonify
from ..utils.pipe_utils import write_to_pipe_with_timeout
from ..utils.logger import log
from config import UPDATE_API_KEY

def handle_update(app, request):
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing Authorization header'}), 401
    
    update_type = request.args.get('type', None)
    
    if update_type not in ['regular', 'force']:
        log.error(f"/update invalid")
        return jsonify({'error': 'Invalid update type'}), 400

    if not hmac.compare_digest(auth_header, UPDATE_API_KEY):
        log.error(f"{update_type.upper()} UPDATE authentication failed")
        return jsonify({'error': f'Invalid token for {update_type} update'}), 401
    
    script = 'update.sh' if update_type == 'regular' else 'force_update.sh'
    if write_to_pipe_with_timeout('/hostpipe/apipipe', script):
        log.info(f"{update_type.upper()} UPDATE called successfully")
        return jsonify({'status': f'{update_type.capitalize()} Update initiated successfully'}), 200
    
    log.error(f"{update_type.upper()} UPDATE failed")
    return jsonify({'error': f'Failed to initiate {update_type} update'}), 500