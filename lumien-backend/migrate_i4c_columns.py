"""
Migration script to add I4C sync columns to bank_responses table
"""
import psycopg2
from app.core.config import settings

def migrate():
    """Add I4C sync columns to bank_responses table"""
    # Convert SQLAlchemy URL to psycopg2 format
    db_url = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        # Check if columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bank_responses' 
            AND column_name = 'i4c_sync_status'
        """)
        
        if cur.fetchone():
            print("I4C sync columns already exist")
            return
        
        # Add new columns
        print("Adding I4C sync columns to bank_responses...")
        
        cur.execute("""
            ALTER TABLE bank_responses 
            ADD COLUMN i4c_sync_status VARCHAR(20) DEFAULT 'PENDING',
            ADD COLUMN i4c_sync_attempted_at TIMESTAMP,
            ADD COLUMN i4c_sync_response_code VARCHAR(10),
            ADD COLUMN i4c_sync_message VARCHAR(255),
            ADD COLUMN i4c_job_id VARCHAR(50)
        """)
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    migrate()
