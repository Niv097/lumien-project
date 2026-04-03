"""
Add missing columns to existing tables
"""
from app.main import engine
from sqlalchemy import text

def add_columns():
    with engine.connect() as conn:
        # Add demo_access to branches
        try:
            conn.execute(text('ALTER TABLE branches ADD COLUMN demo_access BOOLEAN DEFAULT FALSE'))
            conn.commit()
            print('Added demo_access to branches')
        except Exception as e:
            print(f'Note: {e}')
        
        # Add role to users
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'branch_user'"))
            conn.commit()
            print('Added role to users')
        except Exception as e:
            print(f'Note: {e}')

if __name__ == '__main__':
    add_columns()
