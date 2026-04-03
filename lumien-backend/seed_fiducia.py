from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, Role, Bank, User
from app.core.security import get_password_hash
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Create Roles
    roles_list = [
        {"name": "Fiducia Super Admin", "description": "Full platform management"},
        {"name": "Fiducia Operations Manager", "description": "Routing and SLA monitoring"},
        {"name": "Bank HQ Integration User", "description": "Bank-side case processing"},
        {"name": "I4C Observer", "description": "Regulatory read-only access"},
        {"name": "Audit & Compliance Officer", "description": "Audit log and transition review"},
        {"name": "API System Role", "description": "Machine-to-machine ingestion"}
    ]
    
    db_roles = {}
    for r in roles_list:
        role = db.query(Role).filter(Role.name == r["name"]).first()
        if not role:
            role = Role(**r)
            db.add(role)
            db.commit()
            db.refresh(role)
        db_roles[r["name"]] = role

    # 2. Create Banks
    banks_list = [
        {"name": "State Bank of India", "code": "SBI", "ifsc_prefix": "SBIN", "integration_model": "API"},
        {"name": "HDFC Bank", "code": "HDFC", "ifsc_prefix": "HDFC", "integration_model": "ADAPTER"},
        {"name": "ICICI Bank", "code": "ICICI", "ifsc_prefix": "ICIC", "integration_model": "MANUAL"},
        {"name": "Axis Bank", "code": "AXIS", "ifsc_prefix": "UTIB", "integration_model": "API"}
    ]
    
    db_banks = {}
    for b in banks_list:
        bank = db.query(Bank).filter(Bank.code == b["code"]).first()
        if not bank:
            bank = Bank(**b)
            db.add(bank)
            db.commit()
            db.refresh(bank)
        db_banks[b["code"]] = bank

    # 3. Create Super Admin User
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@fiducia.io",
            hashed_password=get_password_hash("fiducia123"),
            is_active=True
        )
        admin_user.roles.append(db_roles["Fiducia Super Admin"])
        db.add(admin_user)
    
    # 4. Create Bank Users (Nodal Branch HQs for each bank)
    for code, bank in db_banks.items():
        username = f"{code.lower()}_nodal"
        bank_user = db.query(User).filter(User.username == username).first()
        if not bank_user:
            bank_user = User(
                username=username,
                email=f"nodal@{code.lower()}.co.in",
                hashed_password=get_password_hash(f"{code.lower()}123"),
                bank_id=bank.id
            )
            bank_user.roles.append(db_roles["Bank HQ Integration User"])
            db.add(bank_user)
            print(f"Created nodal user: {username}")

    db.commit()
    print("FIDUCIA Database seeded successfully.")

if __name__ == "__main__":
    seed()
