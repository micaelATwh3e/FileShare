from flask import Blueprint, request, jsonify, send_file, current_app
from app import db
from app.models import FileUpload, ShareAccess
import os
from datetime import datetime

bp = Blueprint('share', __name__)

@bp.route('/<share_token>/info', methods=['GET'])
def get_share_info(share_token):
    """Get information about a shared file without downloading it"""
    try:
        upload = FileUpload.query.filter_by(
            share_token=share_token,
            is_active=True
        ).first()
        
        if not upload:
            return jsonify({'error': 'File not found'}), 404
        
        # Check if file has expired
        if upload.is_expired():
            return jsonify({'error': 'Share link has expired'}), 410
        
        # Don't reveal recipient email in public info
        info = {
            'id': upload.id,
            'original_name': upload.original_name,
            'size': upload.size,
            'mime_type': upload.mime_type,
            'expires_at': upload.expires_at.isoformat() if upload.expires_at else None,
            'download_count': upload.download_count,
            'max_downloads': upload.max_downloads,
            'has_recipient_restriction': bool(upload.recipient_email),
            'created_at': upload.created_at.isoformat(),
            'uploader_name': upload.uploader.name
        }
        
        return jsonify({'file': info})
        
    except Exception as e:
        current_app.logger.error(f"Share info error: {e}")
        return jsonify({'error': 'Failed to get file info'}), 500

@bp.route('/<share_token>', methods=['GET'])
def download_shared_file(share_token):
    """Download a shared file"""
    try:
        user_email = request.args.get('email', '').strip()
        
        upload = FileUpload.query.filter_by(
            share_token=share_token,
            is_active=True
        ).first()
        
        if not upload:
            return jsonify({'error': 'File not found or link expired'}), 404
        
        # Check if file has expired
        if upload.is_expired():
            return jsonify({'error': 'Share link has expired'}), 410
        
        # Check download limit
        if upload.is_download_limit_reached():
            return jsonify({'error': 'Download limit reached'}), 410
        
        # Check if specific recipient email is required
        if upload.recipient_email and upload.recipient_email != user_email:
            return jsonify({
                'error': 'Access denied. This file is shared with a specific recipient.',
                'requires_email': True
            }), 403
        
        # Check if file exists on filesystem
        if not os.path.exists(upload.upload_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        # Log access if email is provided
        if user_email and upload.recipient_email:
            try:
                share_access = ShareAccess.query.filter_by(
                    share_token=share_token,
                    email=user_email
                ).first()
                
                if share_access:
                    share_access.accessed_at = datetime.utcnow()
                else:
                    share_access = ShareAccess(
                        share_token=share_token,
                        email=user_email
                    )
                    db.session.add(share_access)
                
                db.session.commit()
            except Exception as log_error:
                current_app.logger.error(f"Access logging error: {log_error}")
        
        # Increment download count
        upload.download_count += 1
        db.session.commit()
        
        # Send file
        return send_file(
            upload.upload_path,
            as_attachment=True,
            download_name=upload.original_name,
            mimetype=upload.mime_type
        )
        
    except Exception as e:
        current_app.logger.error(f"Share download error: {e}")
        return jsonify({'error': 'Download failed'}), 500