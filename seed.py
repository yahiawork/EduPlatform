from app import create_app
from app.extensions import db
from app.models import User, Role, Lesson, Exercise

app = create_app()

with app.app_context():
    db.create_all()

    # Seed admin
    if not User.query.filter_by(role=Role.ADMIN).first():
        admin = User(username="yahia", role=Role.ADMIN)
        admin.set_password("ff")
        db.session.add(admin)
        db.session.commit()
        print("Seeded admin: admin / admin123")