"""
Migration script to add i4c_sync_status column to cases table
Run: python migrate_i4c_sync_status.py
"""
from sqlalchemy import text, create_engine
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'cases' AND column_name = 'i4c_sync_status'
    """))
    
    if result.fetchone():
        print("Column i4c_sync_status already exists")
    else:
        print("Adding i4c_sync_status column...")
        conn.execute(text("""
            ALTER TABLE cases 
            ADD COLUMN i4c_sync_status VARCHAR(20) DEFAULT 'PENDING'
        """))
        conn.execute(text("""
            UPDATE cases SET i4c_sync_status = 'PENDING' WHERE i4c_sync_status IS NULL
        """))
        conn.commit()
        print("Column added successfully!")

print("Migration complete")
