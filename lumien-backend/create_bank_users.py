from app.models.models import User, Role, Bank, Branch, get_db
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

def create_bank_users():
    db = next(get_db())
    
    # Get bank role
    bank_role = db.query(Role).filter(Role.name == "Bank HQ Integration User").first()
    if not bank_role:
        bank_role = Role(name="Bank HQ Integration User", description="Bank User")
        db.add(bank_role)
        db.flush()
    
    # Get all banks
    banks = db.query(Bank).all()
    print(f"Found {len(banks)} banks")
    
    created_count = 0
    for bank in banks:
        username = f"{bank.code.lower()}_user"
        
        # Check if already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"  User exists: {username}")
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
        created_count += 1
        print(f"  Created: {username} -> {bank.name} (Branch: {branch.branch_name if branch else 'None'})")
    
    # Create admin user
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
        created_count += 1
        print(f"  Created: admin")
    
    db.commit()
    print(f"\n✅ Total users created: {created_count}")
    print("\n📋 Login Credentials:")
    print("  - Admin: admin / password123")
    for bank in banks:
        print(f"  - {bank.name}: {bank.code.lower()}_user / password123")

if __name__ == "__main__":
    create_bank_users()
