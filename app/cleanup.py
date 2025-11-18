import os
import time
import threading
from datetime import datetime, timedelta
from app import db, create_app
from app.models import FileUpload
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanupService:
    def __init__(self, app=None, interval_hours=1):
        self.app = app
        self.interval_hours = interval_hours
        self._stop_event = threading.Event()
        self._thread = None
    
    def init_app(self, app):
        """Initialize the cleanup service with Flask app"""
        self.app = app
    
    def start(self):
        """Start the background cleanup service"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Cleanup service is already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_cleanup_loop, daemon=True)
        self._thread.start()
        logger.info(f"Cleanup service started with {self.interval_hours} hour interval")
    
    def stop(self):
        """Stop the background cleanup service"""
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join(timeout=5)
            logger.info("Cleanup service stopped")
    
    def _run_cleanup_loop(self):
        """Main cleanup loop that runs in background thread"""
        while not self._stop_event.is_set():
            try:
                with self.app.app_context():
                    self.cleanup_expired_files()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            
            # Wait for next interval or until stop event is set
            self._stop_event.wait(self.interval_hours * 3600)
    
    def cleanup_expired_files(self):
        """Clean up expired files from database and filesystem"""
        try:
            # Find expired uploads
            from datetime import timezone
            expired_uploads = FileUpload.query.filter(
                FileUpload.expires_at < datetime.now(timezone.utc),
                FileUpload.is_active == True
            ).all()
            
            if not expired_uploads:
                logger.info("No expired files to clean up")
                return 0
            
            deleted_count = 0
            for upload in expired_uploads:
                try:
                    # Delete physical file
                    if os.path.exists(upload.upload_path):
                        os.remove(upload.upload_path)
                        logger.info(f"Deleted file: {upload.upload_path}")
                    
                    # Delete database record
                    db.session.delete(upload)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete upload {upload.id}: {e}")
                    continue
            
            # Commit all deletions
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} expired uploads")
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during cleanup: {e}")
            raise

    def cleanup_orphaned_files(self):
        """Clean up files that exist on disk but not in database"""
        try:
            upload_folder = self.app.config.get('UPLOAD_FOLDER')
            if not upload_folder or not os.path.exists(upload_folder):
                return 0
            
            # Get all filenames from database
            db_filenames = set()
            uploads = FileUpload.query.with_entities(FileUpload.upload_path).all()
            for upload in uploads:
                if upload.upload_path:
                    db_filenames.add(os.path.basename(upload.upload_path))
            
            # Check files in upload directory
            deleted_count = 0
            for filename in os.listdir(upload_folder):
                if filename not in db_filenames:
                    file_path = os.path.join(upload_folder, filename)
                    if os.path.isfile(file_path):
                        # Only delete files older than 24 hours to avoid race conditions
                        file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                        if file_age > timedelta(hours=24):
                            os.remove(file_path)
                            logger.info(f"Deleted orphaned file: {file_path}")
                            deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} orphaned files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during orphaned files cleanup: {e}")
            raise

# Global cleanup service instance
cleanup_service = CleanupService()

def init_cleanup_service(app):
    """Initialize and start the cleanup service"""
    cleanup_service.init_app(app)
    
    # Start cleanup service if not in debug mode (to avoid multiple instances during development)
    if not app.debug:
        cleanup_service.start()
    
    return cleanup_service