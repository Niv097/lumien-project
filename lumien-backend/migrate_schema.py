"""
Database migration script to create the new unified cases table
and update existing tables with new fields.
"""

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class SourceType(str, enum.Enum):
    DEMO = "demo"
    I4C = "i4c"

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    HOLD = "HOLD"
    FROZEN = "FROZEN"
    CONFIRMED = "CONFIRMED"
    NOT_RELATED = "NOT_RELATED"
    RECONCILED = "RECONCILED"
    CLOSED = "CLOSED"

class Case(Base):
    """Unified cases table for both demo and I4C cases"""
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    transaction_id = Column(String, index=True)
    amount = Column(Float)
    payment_mode = Column(String)
    payer_account_number = Column(String)
    payer_bank = Column(String)
    mobile_number = Column(String)
    district = Column(String)
    state = Column(String)
    source_type = Column(Enum(SourceType), default=SourceType.DEMO)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledgement_no = Column(String, nullable=True, index=True)

def run_migration():
    # Import from the actual app to get the engine
    import sys
    sys.path.insert(0, 'c:\\Users\\sapra\\Desktop\\LUMIEN\\fiducia-backend')
    from app.main import engine
    
    # Create the cases table
    Base.metadata.create_all(bind=engine, tables=[Case.__table__])
    print("✓ Created 'cases' table")
    
    # Add demo_access column to branches if not exists
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE branches ADD COLUMN demo_access BOOLEAN DEFAULT FALSE"))
            conn.commit()
            print("✓ Added 'demo_access' column to branches")
        except Exception as e:
            print(f"Note: demo_access column may already exist: {e}")
        
        # Add role column to users if not exists
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'branch_user'"))
            conn.commit()
            print("✓ Added 'role' column to users")
        except Exception as e:
            print(f"Note: role column may already exist: {e}")
    
    print("\nMigration completed!")

if __name__ == "__main__":
    run_migration()
