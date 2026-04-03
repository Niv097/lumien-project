from app.models.models import User, Role, Bank, Branch
from app.core.config import settings
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Get or create bank role
bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
if not bank_role:
    bank_role = Role(name="Bank HQ Integration User", description="Bank User")
    db.add(bank_role)
    db.flush()

# Get all banks
banks = db.query(Bank).all()
print(f"Found {len(banks)} banks")

users_created = 0
for bank in banks:
    username = f"{bank.code.lower()}_user"
    
    # Check if user exists
    existing = db.query(User).filter(User.username == username).first()
    if not existing:
        # Get first branch for this bank
        branch = db.query(Branch).filter(Branch.bank_id == bank.id).first()
        
        user = User(
            username=username,
            email=f"{username}@fiducia.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            bank_id=bank.id,
            branch_id=branch.id if branch else None,
            roles=[bank_role]
        )
        db.add(user)
        users_created += 1
        print(f"Created: {username} for {bank.name}")

# Also ensure admin exists
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin_role = db.query(Role).filter(Role.name == "Fiducia Super Admin").first()
    if not admin_role:
        admin_role = Role(name="Fiducia Super Admin", description="Platform Administrator")
        db.add(admin_role)
        db.flush()
    
    admin = User(
        username="admin",
        email="admin@fiducia.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        bank_id=None,
        branch_id=None,
        roles=[admin_role]
    )
    db.add(admin)
    users_created += 1
    print("Created: admin")

db.commit()
print(f"\nTotal users created: {users_created}")
db.close()
