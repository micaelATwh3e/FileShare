<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# File Upload and Sharing System

This project is a web application for secure file upload and sharing with the following features:

## Core Features
- User registration and authentication
- File upload with 100MB max size limit
- Secure file sharing with unique tokens
- Email notifications for file shares
- Configurable file expiration times
- Admin panel for user management

## Technology Stack
- Backend: Node.js with Express
- Database: PostgreSQL with Prisma ORM
- Authentication: JWT tokens
- File Storage: Local storage with UUID naming
- Email: Nodemailer for notifications
- Frontend: React with TypeScript
- Styling: Tailwind CSS

## Security Features
- Unique, cryptographically secure tokens for file shares
- JWT-based authentication
- File access control based on email permissions
- Secure file storage with UUID naming
- Rate limiting and file size validation

## User Roles
- **Regular Users**: Can upload files and share with specific email addresses
- **Admins**: Can manage users, view all uploads, and system administration

## Project Status
✅ Complete Python Flask file upload and sharing system
✅ User authentication with JWT tokens
✅ Secure file sharing with unique tokens
✅ Email notifications for file shares
✅ Admin panel for user management
✅ Frontend web interface
✅ SQLite database for development
✅ Ready to run and test