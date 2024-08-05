import random
from flask import jsonify

def handle_data(request):
    request_info = {
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "origin": request.headers.get("Origin"),
        "remote_addr": request.remote_addr,
        "user_agent": request.user_agent.string
    }
    response_data = {"number": random.randrange(100)}
    return jsonify(response_data), 200