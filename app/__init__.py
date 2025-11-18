from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from config import Config
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, origins=['*'], supports_credentials=True)  # Allow all origins for development
    mail.init_app(app)
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    from app.upload import bp as upload_bp
    from app.admin import bp as admin_bp
    from app.share import bp as share_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(share_bp, url_prefix='/share')
    
    # Initialize cleanup service
    from app.cleanup import init_cleanup_service
    init_cleanup_service(app)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'OK', 'message': 'File upload service is running'}
    
    # Debug timezone endpoint
    @app.route('/api/debug/timezone')
    def debug_timezone():
        from datetime import datetime, timezone, timedelta
        import time
        
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()
        
        # Calculate what 1 hour from now would be
        expires_in_1h = now_utc + timedelta(hours=1)
        
        return {
            'server_utc_time': now_utc.isoformat(),
            'server_local_time': now_local.isoformat(),
            'timezone_offset_hours': time.timezone / 3600,
            'dst_active': time.daylight,
            'example_1h_expiration': expires_in_1h.isoformat(),
            'is_expired_check': now_utc > expires_in_1h
        }
    
    # Serve frontend
    @app.route('/')
    def index():
        from flask import send_from_directory
        import os
        return send_from_directory(os.path.join(app.root_path, '..', 'templates'), 'index.html')
    
    return app

# Import models after db initialization to avoid circular imports
from app import models