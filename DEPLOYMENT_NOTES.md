# Deployment Notes

## Configuration Fixes Applied

### Issue: Download Limit Reached on First Attempt
- **Problem**: Files were being created with `max_downloads=1` by default, causing "limit reached" error on first download
- **Solution**: Updated database to set `max_downloads=NULL` for unlimited downloads on existing files
- **Prevention**: Frontend form properly sends empty value for unlimited downloads

### Issue: File Not Found Errors
- **Problem**: Upload paths were stored as relative paths but resolved from Flask app directory
- **Solution**: 
  - Set `UPLOAD_FOLDER=/home/iwery/upload/uploads` (absolute path) in `.env`
  - Updated existing database records to use absolute file paths
  - Files now properly resolve for downloads

### Required .env Configuration
```
DATABASE_URL=sqlite:////home/iwery/upload/instance/fileupload.db
UPLOAD_FOLDER=/home/iwery/upload/uploads
```

Both paths must be absolute when running in production to ensure proper file resolution.