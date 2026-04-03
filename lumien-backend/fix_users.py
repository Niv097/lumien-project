from app.models.models import User, Role, Bank, Branch
from app.core.config import settings
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== CREATING BANK USERS ===")

# Get bank role
bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
if not bank_role:
    bank_role = Role(name="Bank HQ Integration User", description="Bank User")
    db.add(bank_role)
    db.flush()
    print("Created: Bank HQ Integration User role")

# Get all banks
banks = db.query(Bank).all()
print(f"Found {len(banks)} banks\n")

# Delete old weird users (1_user, 2_user, etc.)
old_users = db.query(User).filter(User.username.like('%_user')).all()
for u in old_users:
    # Check if it's a valid bank code user
    is_valid = False
    for bank in banks:
        if u.username == f"{bank.code.lower()}_user":
            is_valid = True
            break
    if not is_valid and u.username != 'admin':
        print(f"Deleting invalid user: {u.username}")
        db.delete(u)

db.commit()

# Create proper bank users
for bank in banks:
    username = f"{bank.code.lower()}_user"
    
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"User exists: {username} -> {bank.name}")
        continue
    
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
    print(f"Created: {username} -> {bank.name} (Branch: {branch.branch_name if branch else 'None'})")

# Create admin
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
    print("Created: admin")

db.commit()

# Verify
print("\n=== VERIFICATION ===")
users = db.query(User).all()
print(f"Total users: {len(users)}")
for u in users:
    bank_name = "N/A"
    if u.bank_id:
        bank = db.query(Bank).filter(Bank.id == u.bank_id).first()
        bank_name = bank.name if bank else "Unknown"
    print(f"  - {u.username} -> {bank_name}")

db.close()
print("\n✅ Done! You can now login with any {bank_code}_user / password123")
