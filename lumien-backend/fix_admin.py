from app.models.models import User, Role
from app.core.config import settings
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Fix admin user
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    admin.hashed_password = get_password_hash("admin")
    db.commit()
    print(f"✅ Admin password reset to: admin")
else:
    # Create admin
    admin_role = db.query(Role).filter(Role.name == "Fiducia Super Admin").first()
    if not admin_role:
        admin_role = Role(name="Fiducia Super Admin", description="Platform Administrator")
        db.add(admin_role)
        db.flush()
    
    admin = User(
        username="admin",
        email="admin@fiducia.com",
        hashed_password=get_password_hash("admin"),
        is_active=True
    )
    admin.roles.append(admin_role)
    db.add(admin)
    db.commit()
    print(f"✅ Admin user created: admin / admin")

# List all users
print("\n📋 All users in database:")
users = db.query(User).all()
for u in users:
    print(f"   - {u.username} (Bank: {u.bank_id}, Active: {u.is_active})")

db.close()
