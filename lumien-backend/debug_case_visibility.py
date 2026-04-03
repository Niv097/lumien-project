from app.models.models import User, Case, Branch
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("=== DEBUGGING CASE VISIBILITY ===\n")

# Check yes_user
user = db.query(User).filter(User.username == "yes_user").first()
if user:
    print(f"✅ yes_user found:")
    print(f"   Bank ID: {user.bank_id}")
    print(f"   Branch ID: {user.branch_id}")
    
    if user.branch_id:
        branch = db.query(Branch).filter(Branch.id == user.branch_id).first()
        if branch:
            print(f"   Branch Name: {branch.branch_name}")
            print(f"   Demo Access: {branch.demo_access}")
else:
    print("❌ yes_user NOT FOUND")

# Check all cases
print(f"\n📊 Total cases in database: {db.query(Case).count()}")

# Check cases by source
i4c_cases = db.query(Case).filter(Case.source_type == "i4c").all()
demo_cases = db.query(Case).filter(Case.source_type == "demo").all()
print(f"   I4C cases: {len(i4c_cases)}")
print(f"   Demo cases: {len(demo_cases)}")

# Check unassigned cases (no branch_id)
unassigned = db.query(Case).filter(Case.branch_id.is_(None)).all()
print(f"\n🔍 Unassigned cases (no branch): {len(unassigned)}")
for c in unassigned[:5]:
    print(f"   - {c.case_id} | Source: {c.source_type} | Status: {c.status}")

# Check cases assigned to yes_user's branch
if user and user.branch_id:
    assigned_cases = db.query(Case).filter(Case.branch_id == user.branch_id).all()
    print(f"\n📁 Cases assigned to yes_user's branch ({user.branch_id}): {len(assigned_cases)}")
    for c in assigned_cases[:5]:
        print(f"   - {c.case_id} | Status: {c.status}")

print("\n💡 SOLUTION: Need to assign I4C cases to yes_user's branch")
print("   Or enable demo_access for the branch to see unassigned demo cases")

db.close()
