from app import db
from datetime import datetime
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploads = db.relationship('FileUpload', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    mime_type = db.Column(db.String(100))
    size = db.Column(db.BigInteger, nullable=False)
    upload_path = db.Column(db.String(500), nullable=False)
    share_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    recipient_email = db.Column(db.String(120))
    expires_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    max_downloads = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    uploader_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    def is_download_limit_reached(self):
        return self.max_downloads and self.download_count >= self.max_downloads
    
    def to_dict(self):
        return {
            'id': self.id,
            'original_name': self.original_name,
            'size': self.size,
            'mime_type': self.mime_type,
            'share_token': self.share_token,
            'recipient_email': self.recipient_email,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'download_count': self.download_count,
            'max_downloads': self.max_downloads,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'uploader': {
                'name': self.uploader.name,
                'email': self.uploader.email
            } if self.uploader else None
        }
    
    def __repr__(self):
        return f'<FileUpload {self.original_name}>'

class ShareAccess(db.Model):
    __tablename__ = 'share_access'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    share_token = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('share_token', 'email', name='unique_share_access'),)
    
    def __repr__(self):
        return f'<ShareAccess {self.email} -> {self.share_token}>'