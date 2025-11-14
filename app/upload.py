from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db, mail
from app.models import User, FileUpload
from flask_mail import Message
import os
import uuid
from datetime import datetime, timedelta
import secrets

bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_share_notification(recipient_email, sender_name, filename, share_token, expires_at=None):
    """Send email notification for file share"""
    current_app.logger.info(f"=== EMAIL DEBUGGING START ===")
    current_app.logger.info(f"Recipient: {recipient_email}")
    current_app.logger.info(f"Sender: {sender_name}")
    current_app.logger.info(f"Filename: {filename}")
    
    # Log all mail configuration
    current_app.logger.info(f"MAIL_SERVER: {current_app.config.get('MAIL_SERVER')}")
    current_app.logger.info(f"MAIL_PORT: {current_app.config.get('MAIL_PORT')}")
    current_app.logger.info(f"MAIL_USE_SSL: {current_app.config.get('MAIL_USE_SSL')}")
    current_app.logger.info(f"MAIL_USE_TLS: {current_app.config.get('MAIL_USE_TLS')}")
    current_app.logger.info(f"MAIL_USERNAME: {current_app.config.get('MAIL_USERNAME')}")
    current_app.logger.info(f"MAIL_PASSWORD configured: {'Yes' if current_app.config.get('MAIL_PASSWORD') else 'No'}")
    current_app.logger.info(f"MAIL_DEFAULT_SENDER: {current_app.config.get('MAIL_DEFAULT_SENDER')}")
    
    # Skip email if MAIL_SERVER is not configured properly
    if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
        current_app.logger.warning("Email not configured - missing username or password")
        return False
    
    try:
        current_app.logger.info("Creating message...")
        # Use request host if available, otherwise fall back to config
        from flask import request
        if request and request.headers.get('Host'):
            protocol = 'https' if request.is_secure else 'http'
            base_url = f"{protocol}://{request.headers.get('Host')}/share/{share_token}"
        else:
            base_url = f"{current_app.config['CLIENT_URL']}/share/{share_token}"
        
        # Add email parameter if there's a specific recipient
        if recipient_email:
            from urllib.parse import quote
            download_url = f"{base_url}?email={quote(recipient_email)}"
        else:
            download_url = base_url
        current_app.logger.info(f"Download URL: {download_url}")
        
        expiration_text = ""
        if expires_at:
            expiration_text = f"This link will expire on {expires_at.strftime('%Y-%m-%d at %H:%M')}."
            current_app.logger.info(f"Expiration text: {expiration_text}")
        
        msg = Message(
            subject=f"{sender_name} shared a file with you: {filename}",
            recipients=[recipient_email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>You've received a file share!</h2>
                <p>Hello,</p>
                <p><strong>{sender_name}</strong> has shared a file with you:</p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0;">📎 {filename}</h3>
                    <a href="{download_url}" 
                       style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Download File
                    </a>
                </div>
                
                <p><strong>Download Link:</strong> <a href="{download_url}">{download_url}</a></p>
                
                {f'<p><em>{expiration_text}</em></p>' if expiration_text else ''}
                
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                    If you didn't expect this file, you can safely ignore this message.
                </p>
            </div>
            """
        )
        
        current_app.logger.info(f"Message created - Subject: {msg.subject}")
        current_app.logger.info(f"Message recipients: {msg.recipients}")
        current_app.logger.info(f"Message sender: {msg.sender}")
        
        current_app.logger.info("Attempting to send email via Flask-Mail...")
        
        # Test SMTP connection first
        try:
            import smtplib
            import ssl
            
            current_app.logger.info("Testing raw SMTP connection...")
            
            if current_app.config.get('MAIL_USE_SSL'):
                current_app.logger.info("Using SSL connection...")
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    current_app.config['MAIL_SERVER'], 
                    current_app.config['MAIL_PORT'], 
                    context=context
                )
            else:
                current_app.logger.info("Using TLS connection...")
                server = smtplib.SMTP(
                    current_app.config['MAIL_SERVER'], 
                    current_app.config['MAIL_PORT']
                )
                if current_app.config.get('MAIL_USE_TLS'):
                    server.starttls()
            
            current_app.logger.info("SMTP connection established, attempting login...")
            server.login(
                current_app.config['MAIL_USERNAME'], 
                current_app.config['MAIL_PASSWORD']
            )
            current_app.logger.info("SMTP login successful")
            server.quit()
            current_app.logger.info("Raw SMTP test completed successfully")
            
        except Exception as smtp_e:
            current_app.logger.error(f"Raw SMTP test failed: {smtp_e}")
            current_app.logger.error(f"Exception type: {type(smtp_e).__name__}")
            import traceback
            current_app.logger.error(f"SMTP traceback: {traceback.format_exc()}")
            
            # If raw SMTP fails, don't continue with Flask-Mail
            current_app.logger.error("Skipping Flask-Mail attempt due to raw SMTP failure")
            current_app.logger.error(f"=== EMAIL DEBUGGING END (FAILED) ===")
            return False
        
        # Now try Flask-Mail
        current_app.logger.info("Sending via Flask-Mail...")
        try:
            mail.send(msg)
            current_app.logger.info(f"✅ Email sent successfully via Flask-Mail to {recipient_email}")
            current_app.logger.info(f"=== EMAIL DEBUGGING END (SUCCESS) ===")
            return True
        except Exception as flask_mail_error:
            current_app.logger.error(f"Flask-Mail failed: {flask_mail_error}")
            current_app.logger.info("Trying direct smtplib as fallback...")
            
            # Fallback to direct smtplib
            try:
                import smtplib
                import ssl
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                context = ssl.create_default_context()
                
                with smtplib.SMTP_SSL(
                    current_app.config['MAIL_SERVER'], 
                    current_app.config['MAIL_PORT'], 
                    context=context
                ) as server:
                    server.login(
                        current_app.config['MAIL_USERNAME'], 
                        current_app.config['MAIL_PASSWORD']
                    )
                    
                    # Create email message
                    email_msg = MIMEMultipart('alternative')
                    email_msg['Subject'] = msg.subject
                    email_msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
                    email_msg['To'] = recipient_email
                    
                    # Add HTML content
                    html_part = MIMEText(msg.html, 'html')
                    email_msg.attach(html_part)
                    
                    # Send email
                    server.send_message(email_msg)
                    current_app.logger.info(f"✅ Email sent successfully via direct smtplib to {recipient_email}")
                    current_app.logger.info(f"=== EMAIL DEBUGGING END (SUCCESS) ===")
                    return True
                    
            except Exception as smtplib_error:
                current_app.logger.error(f"Direct smtplib also failed: {smtplib_error}")
                current_app.logger.error(f"=== EMAIL DEBUGGING END (FAILED) ===")
                return False
        
    except Exception as e:
        current_app.logger.error(f"❌ Email sending failed: {e}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        current_app.logger.error(f"=== EMAIL DEBUGGING END (FAILED) ===")
        return False

@bp.route('/', methods=['POST'])
@jwt_required()
def upload_file():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get additional form data
        recipient_email = request.form.get('recipient_email', '').strip()
        expiration_hours = request.form.get('expiration_hours', type=int)
        max_downloads = request.form.get('max_downloads', type=int)
        
        # Validate recipient email if provided
        if recipient_email:
            from email_validator import validate_email, EmailNotValidError
            try:
                validate_email(recipient_email)
            except EmailNotValidError:
                return jsonify({'error': 'Invalid recipient email format'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Generate secure share token
        share_token = secrets.token_urlsafe(32)
        
        # Calculate expiration date
        expires_at = None
        if expiration_hours and expiration_hours > 0:
            expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        # Save file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        # Get file size
        file_size = os.path.getsize(upload_path)
        
        # Create database record
        file_upload = FileUpload(
            original_name=original_filename,
            filename=unique_filename,
            mime_type=file.content_type or 'application/octet-stream',
            size=file_size,
            upload_path=upload_path,
            share_token=share_token,
            recipient_email=recipient_email if recipient_email else None,
            expires_at=expires_at,
            max_downloads=max_downloads,
            uploader_id=user_id
        )
        
        db.session.add(file_upload)
        db.session.commit()
        
        # Send email notification if recipient email is provided
        if recipient_email:
            send_share_notification(
                recipient_email=recipient_email,
                sender_name=user.name,
                filename=original_filename,
                share_token=share_token,
                expires_at=expires_at
            )
        
        return jsonify({
            'message': 'File uploaded successfully',
            'upload': file_upload.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Upload error: {e}")
        
        # Clean up file if it was saved
        if 'upload_path' in locals() and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except:
                pass
        
        return jsonify({'error': 'Upload failed'}), 500

@bp.route('/my-uploads', methods=['GET'])
@jwt_required()
def get_my_uploads():
    try:
        user_id = get_jwt_identity()
        
        uploads = FileUpload.query.filter_by(
            uploader_id=user_id,
            is_active=True
        ).order_by(FileUpload.created_at.desc()).all()
        
        return jsonify({
            'uploads': [upload.to_dict() for upload in uploads]
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch uploads'}), 500

@bp.route('/<upload_id>', methods=['DELETE'])
@jwt_required()
def delete_upload(upload_id):
    try:
        user_id = get_jwt_identity()
        
        upload = FileUpload.query.filter_by(
            id=upload_id,
            uploader_id=user_id
        ).first()
        
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404
        
        # Delete file from filesystem
        if os.path.exists(upload.upload_path):
            try:
                os.remove(upload.upload_path)
            except Exception as e:
                current_app.logger.error(f"File deletion error: {e}")
        
        # Mark as inactive in database
        upload.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Upload deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete upload'}), 500