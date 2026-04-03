"""Fix users - create proper bank users for login"""
import sys
sys.path.insert(0, r'C:\Users\sapra\Desktop\LUMIEN\fiducia-backend')

from app.models.models import User, Role, Bank, Branch
from app.core.config import settings
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== FIXING USERS ===")

# Get bank role
bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
if not bank_role:
    bank_role = Role(name="Bank HQ Integration User", description="Bank User")
    db.add(bank_role)
    db.flush()
    print("Created bank role")

# Get all banks
banks = db.query(Bank).all()
print(f"Found {len(banks)} banks")

created = 0
for bank in banks:
    username = f"{bank.code.lower()}_user"
    
    # Check if exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"  EXISTS: {username}")
        continue
    
    # Get branch for this bank
    branch = db.query(Branch).filter(Branch.bank_id == bank.id).first()
    
    # Create user
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
    created += 1
    print(f"  CREATED: {username} -> {bank.name}")

# Create admin
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin_role = db.query(Role).filter(Role.name == "Fiducia Super Admin").first()
    if not admin_role:
        admin_role = Role(name="Fiducia Super Admin", description="Admin")
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
    created += 1
    print("  CREATED: admin")

db.commit()
print(f"\n✅ Created {created} users")

# Verify
print("\n=== USERS IN DATABASE ===")
users = db.query(User).all()
for u in users:
    bank = db.query(Bank).filter(Bank.id == u.bank_id).first() if u.bank_id else None
    bank_name = bank.name if bank else "Admin"
    print(f"  {u.username} -> {bank_name}")

db.close()
print("\n✅ Done! Login with: {bank_code}_user / password123")
