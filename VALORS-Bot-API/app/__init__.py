from flask import Flask
from flask_cors import CORS
from .models import init_db
from .routes import init_routes
import redis
from datetime import datetime, timezone
from .utils.logger import log

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {
        "origins": ["https://valorsleague.org"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Set logger level
    log.set_level(log.DEBUG if app.config['DEBUG'] else log.INFO)
    
    # Initialize database
    init_db(app)
    
    # Initialize Redis
    app.redis_db = redis.StrictRedis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        decode_responses=True
    )
    
    # Initialize routes
    init_routes(app)
    
    log.info(f"Server started at {datetime.now(timezone.utc)}")
    
    return app