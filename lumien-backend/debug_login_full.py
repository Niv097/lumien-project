from app.models.models import User, Role, Bank, Branch
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== CHECKING USERS IN DATABASE ===")
users = db.query(User).all()
print(f"Total users: {len(users)}")
print()

if users:
    for u in users[:10]:
        print(f"User: {u.username}")
        print(f"  Email: {u.email}")
        print(f"  Bank ID: {u.bank_id}")
        print(f"  Branch ID: {u.branch_id}")
        print(f"  Is Active: {u.is_active}")
        print(f"  Password hash: {u.hashed_password[:40]}...")
        # Test password
        is_valid = verify_password("password123", u.hashed_password)
        print(f"  Password 'password123' valid: {is_valid}")
        print()
else:
    print("NO USERS FOUND IN DATABASE!")
    print("Need to create users...")

# Check if yes_user exists specifically
yes_user = db.query(User).filter(User.username == "yes_user").first()
print("=== CHECKING yes_user ===")
if yes_user:
    print(f"yes_user exists: {yes_user.username}")
    print(f"  Bank ID: {yes_user.bank_id}")
    print(f"  Password valid: {verify_password('password123', yes_user.hashed_password)}")
else:
    print("yes_user NOT FOUND!")
    
    # Create yes_user
    print("\nCreating yes_user...")
    bank = db.query(Bank).filter(Bank.code == "YES").first()
    if bank:
        print(f"  Found YES bank: {bank.name} (ID: {bank.id})")
        branch = db.query(Branch).filter(Branch.bank_id == bank.id).first()
        if branch:
            print(f"  Found branch: {branch.branch_name} (ID: {branch.id})")
        
        bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
        if not bank_role:
            bank_role = Role(name="Bank HQ Integration User", description="Bank User")
            db.add(bank_role)
            db.flush()
        
        new_user = User(
            username="yes_user",
            email="yes_user@fiducia.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            bank_id=bank.id,
            branch_id=branch.id if branch else None,
            roles=[bank_role]
        )
        db.add(new_user)
        db.commit()
        print(f"  Created yes_user successfully!")
    else:
        print("  ERROR: YES bank not found!")

db.close()
print("\nDone!")
