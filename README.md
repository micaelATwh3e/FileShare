# File Upload and Sharing System

A secure Python Flask application for file upload and sharing with user authentication, expiration controls, and email notifications.

## Features

- 🔐 **User Authentication**: JWT-based login/registration system
- 📁 **File Upload**: Support for files up to 100MB
- 🔗 **Secure Sharing**: Unique cryptographically secure share tokens
- ⏰ **Expiration Control**: Set custom expiration times for shares
- 📧 **Email Notifications**: Automatic email notifications to recipients
- 👨‍💼 **Admin Panel**: User management and system statistics
- 🚫 **Access Control**: Restrict downloads to specific email addresses
- 📊 **Download Tracking**: Monitor download counts and access logs

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with Flask-JWT-Extended
- **File Storage**: Local file system with UUID naming
- **Email**: Flask-Mail with SMTP support
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- SMTP email account (Gmail, etc.)

### Installation

1. **Clone and setup**:
   ```bash
   cd /home/iwery/upload
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database and email settings
   ```

3. **Setup database**:
   ```bash
   # Create PostgreSQL database named 'fileupload_db'
   # Update DATABASE_URL in .env
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

5. **Access the application**:
   - Open http://localhost:5000
   - Default admin: admin@example.com / admin123

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `UPLOAD_FOLDER` | Directory for uploaded files | No (default: uploads) |
| `MAIL_SERVER` | SMTP server hostname | Yes for email |
| `MAIL_USERNAME` | SMTP username | Yes for email |
| `MAIL_PASSWORD` | SMTP password | Yes for email |
| `CLIENT_URL` | Frontend URL for email links | No |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### File Upload
- `POST /api/upload/` - Upload a file
- `GET /api/upload/my-uploads` - Get user's uploads
- `DELETE /api/upload/<id>` - Delete an upload

### File Sharing
- `GET /api/share/<token>/info` - Get file info
- `GET /api/share/<token>` - Download shared file

### Admin (Admin Only)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/<id>` - Update user
- `DELETE /api/admin/users/<id>` - Delete user
- `GET /api/admin/uploads` - List all uploads
- `GET /api/admin/stats` - System statistics

## File Upload Features

### Upload Form Fields
- **File**: Select file up to 100MB
- **Recipient Email**: Optional - restrict access to specific email
- **Expiration Hours**: Optional - set automatic expiration (1-8760 hours)
- **Max Downloads**: Optional - limit number of downloads

### Security Features
- Unique 256-bit share tokens (impossible to guess)
- JWT-based authentication
- File access control by email
- Secure file storage with UUID naming
- Input validation and sanitization
- CORS protection

## User Roles

### Regular Users
- Upload files and create shares
- Set expiration times and download limits
- Share with specific email addresses
- View their own upload history

### Admin Users
- All regular user features
- Manage user accounts (create/edit/delete)
- View all uploads and statistics
- System administration

## Email Notifications

When a file is shared with a specific email address, the recipient receives:
- Notification email with download link
- File name and sender information
- Expiration details (if set)
- Direct download button

## Development

### Project Structure
```
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── auth.py              # Authentication routes
│   ├── upload.py            # File upload routes
│   ├── share.py             # File sharing routes
│   └── admin.py             # Admin routes
├── templates/
│   └── index.html           # Frontend interface
├── uploads/                 # Uploaded files directory
├── config.py                # Configuration
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── .env.example            # Environment variables template
```

### Database Models
- **User**: User accounts with authentication
- **FileUpload**: File metadata and sharing info
- **ShareAccess**: Download access logging

## Security Considerations

- Store sensitive data in environment variables
- Use strong JWT secrets
- Configure HTTPS in production
- Set up proper CORS policies
- Implement rate limiting
- Regular security updates
- Secure file storage location
- Input validation and sanitization

## Production Deployment

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Set up reverse proxy (Nginx)
3. Configure HTTPS/SSL
4. Use production database
5. Set up monitoring and logging
6. Configure backup strategy
7. Implement proper security headers

## License

MIT License - see LICENSE file for details