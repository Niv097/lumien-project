from app.models.models import User, Case, Branch
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Get yes_user's branch
user = db.query(User).filter(User.username == "yes_user").first()
if not user or not user.branch_id:
    print("❌ yes_user or branch not found")
    db.close()
    exit()

branch_id = user.branch_id
branch = db.query(Branch).filter(Branch.id == branch_id).first()
print(f"✅ Assigning cases to {branch.branch_name} (ID: {branch_id})\n")

# Get all unassigned I4C and demo cases
unassigned_cases = db.query(Case).filter(Case.branch_id.is_(None)).all()
print(f"Found {len(unassigned_cases)} unassigned cases")

assigned_count = 0
for case in unassigned_cases:
    case.branch_id = branch_id
    assigned_count += 1
    if assigned_count <= 5:
        print(f"   ✓ Assigned: {case.case_id}")

if assigned_count > 5:
    print(f"   ... and {assigned_count - 5} more")

db.commit()
print(f"\n✅ Successfully assigned {assigned_count} cases to your branch!")
print("🔄 Refresh the Case Inbox page to see them.")

db.close()
