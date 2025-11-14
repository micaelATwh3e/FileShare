from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
from email_validator import validate_email, EmailNotValidError
import bcrypt

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        # Check if open registration is allowed
        from flask import current_app
        if not current_app.config.get('ALLOW_OPEN_REGISTRATION', False):
            return jsonify({'error': 'Registration is disabled. Please contact an administrator.'}), 403
        
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('email', 'password', 'name')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        
        # Validate email format
        try:
            validate_email(email)
        except EmailNotValidError:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            is_admin=False
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Missing email or password'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()})
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user info'}), 500

@bp.route('/registration-status', methods=['GET'])
def registration_status():
    """Check if registration is enabled"""
    from flask import current_app
    return jsonify({
        'registration_enabled': current_app.config.get('ALLOW_OPEN_REGISTRATION', False)
    })