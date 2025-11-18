from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, FileUpload
from email_validator import validate_email, EmailNotValidError
import bcrypt

bp = Blueprint('admin', __name__)

def require_admin(f):
    """Decorator to require admin privileges"""
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin
def get_all_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        users_query = User.query.order_by(User.created_at.desc())
        users = users_query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch users'}), 500

@bp.route('/users', methods=['POST'])
@jwt_required()
@require_admin
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not all(k in data for k in ('email', 'password', 'name')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        is_admin = data.get('is_admin', False)
        
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
            is_admin=is_admin
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500

@bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
@require_admin
def update_user(user_id):
    """Update an existing user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields if provided
        if 'email' in data:
            email = data['email'].lower().strip()
            try:
                validate_email(email)
            except EmailNotValidError:
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Check for email conflicts
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already in use'}), 400
            
            user.email = email
        
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'is_admin' in data:
            user.is_admin = bool(data['is_admin'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500

@bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_user(user_id):
    """Delete a user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Prevent admin from deleting themselves
        if user_id == current_user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

@bp.route('/uploads', methods=['GET'])
@jwt_required()
@require_admin
def get_all_uploads():
    """Get all uploads with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        uploads_query = FileUpload.query.order_by(FileUpload.created_at.desc())
        uploads = uploads_query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'uploads': [upload.to_dict() for upload in uploads.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': uploads.total,
                'pages': uploads.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch uploads'}), 500

@bp.route('/uploads/<upload_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def delete_upload(upload_id):
    """Delete a file upload"""
    try:
        upload = FileUpload.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Delete physical file
        import os
        if os.path.exists(upload.upload_path):
            os.remove(upload.upload_path)
        
        # Delete database record
        db.session.delete(upload)
        db.session.commit()
        
        return jsonify({'message': 'Upload deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete upload'}), 500

@bp.route('/cleanup-expired', methods=['POST'])
@jwt_required()
@require_admin
def cleanup_expired_uploads():
    """Manually trigger cleanup of expired uploads"""
    try:
        from datetime import datetime, timezone
        import os
        
        # Find expired uploads using model method to avoid timezone issues
        all_uploads = FileUpload.query.filter_by(is_active=True).all()
        expired_uploads = [upload for upload in all_uploads if upload.is_expired()]
        
        deleted_count = 0
        for upload in expired_uploads:
            # Delete physical file
            if os.path.exists(upload.upload_path):
                try:
                    os.remove(upload.upload_path)
                except OSError:
                    pass  # File might already be deleted
            
            # Delete database record
            db.session.delete(upload)
            deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Cleaned up {deleted_count} expired uploads',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cleanup expired uploads'}), 500

@bp.route('/stats', methods=['GET'])
@jwt_required()
@require_admin
def get_system_stats():
    """Get system statistics"""
    try:
        from datetime import datetime, timezone
        
        total_users = User.query.count()
        total_uploads = FileUpload.query.count()
        active_uploads = FileUpload.query.filter_by(is_active=True).count()
        
        # Count expired uploads using model method to avoid timezone issues
        all_uploads = FileUpload.query.filter_by(is_active=True).all()
        expired_uploads = sum(1 for upload in all_uploads if upload.is_expired())
        
        # Calculate total file size
        total_size_result = db.session.query(db.func.sum(FileUpload.size)).filter_by(is_active=True).scalar()
        total_size = total_size_result or 0
        
        return jsonify({
            'total_users': total_users,
            'total_uploads': total_uploads,
            'active_uploads': active_uploads,
            'expired_uploads': expired_uploads,
            'total_size': total_size
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch statistics'}), 500