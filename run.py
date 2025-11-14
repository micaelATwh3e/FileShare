from app import create_app, db
from app.models import User, FileUpload, ShareAccess

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create a default admin user if none exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            import bcrypt
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin = User(
                email='admin@example.com',
                password_hash=admin_password,
                name='Admin User',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user: admin@example.com / admin123")
    
    app.run(debug=True, host='0.0.0.0', port=11000)