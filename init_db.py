from factory import create_app, db

# Create the Flask app instance
app = create_app()

# Create all database tables
with app.app_context():
    db.create_all()
    print("✅ All tables created successfully.")

