from app.models.models import User, Role, Bank, Branch
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== DEBUG LOGIN ===")
print(f"Database URL: {settings.DATABASE_URL}")
print()

# Check all users
users = db.query(User).all()
print(f"Total users: {len(users)}")
for u in users:
    print(f"  User: {u.username}, Bank ID: {u.bank_id}, Branch ID: {u.branch_id}, Active: {u.is_active}")
    # Test password verification
    test_password = "password123"
    is_valid = verify_password(test_password, u.hashed_password)
    print(f"    Password 'password123' valid: {is_valid}")
    print(f"    Hashed password: {u.hashed_password[:50]}...")

print()
print("=== TESTING YES BANK USER ===")
yes_user = db.query(User).filter(User.username == "yes_user").first()
if yes_user:
    print(f"Found yes_user: {yes_user.username}")
    print(f"Bank ID: {yes_user.bank_id}")
    
    # Get bank
    if yes_user.bank_id:
        bank = db.query(Bank).filter(Bank.id == yes_user.bank_id).first()
        print(f"Bank: {bank.name if bank else 'NOT FOUND'}")
    
    # Test password
    is_valid = verify_password("password123", yes_user.hashed_password)
    print(f"Password valid: {is_valid}")
else:
    print("yes_user NOT FOUND!")

db.close()
