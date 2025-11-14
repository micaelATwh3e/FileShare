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
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'OK', 'message': 'File upload service is running'}
    
    # Serve frontend
    @app.route('/')
    def index():
        from flask import send_from_directory
        import os
        return send_from_directory(os.path.join(app.root_path, '..', 'templates'), 'index.html')
    
    return app

# Import models after db initialization to avoid circular imports
from app import models