#!/usr/bin/env python3
"""Fix hdfc_user branch assignment - run this directly"""
import sys
sys.path.insert(0, r'c:\Users\sapra\Desktop\LUMIEN\fiducia-backend')

from sqlalchemy import create_engine, text

# Connect to database
engine = create_engine('postgresql://postgres:password@localhost:5432/fiducia_saas')

with engine.connect() as conn:
    # Check if hdfc_user exists and get their current branch
    result = conn.execute(text("SELECT id, username, branch_id FROM users WHERE username = 'hdfc_user'"))
    user = result.fetchone()
    
    if not user:
        print("hdfc_user not found - need to create")
        # Get or create HDFC bank
        bank_result = conn.execute(text("SELECT id FROM banks WHERE code = 'HDFC'"))
        bank = bank_result.fetchone()
        if not bank:
            conn.execute(text("INSERT INTO banks (name, code, ifsc_prefix, is_active) VALUES ('HDFC Bank', 'HDFC', 'HDFC', true)"))
            conn.commit()
            bank_result = conn.execute(text("SELECT id FROM banks WHERE code = 'HDFC'"))
            bank = bank_result.fetchone()
        bank_id = bank[0]
        print(f"HDFC Bank ID: {bank_id}")
        
        # Get or create HDFC branch
        branch_result = conn.execute(text("SELECT id FROM branches WHERE bank_id = :bank_id"), {"bank_id": bank_id})
        branch = branch_result.fetchone()
        if not branch:
            conn.execute(text("""
                INSERT INTO branches (bank_id, branch_code, branch_name, ifsc_code, demo_access, is_active) 
                VALUES (:bank_id, 'HDFC001', 'HDFC Main Branch', 'HDFC0000001', true, true)
            """), {"bank_id": bank_id})
            conn.commit()
            branch_result = conn.execute(text("SELECT id FROM branches WHERE bank_id = :bank_id"), {"bank_id": bank_id})
            branch = branch_result.fetchone()
        branch_id = branch[0]
        print(f"HDFC Branch ID: {branch_id}")
        
        # Create hdfc_user
        from app.core.security import get_password_hash
        hashed_pw = get_password_hash('hdfc123')
        conn.execute(text("""
            INSERT INTO users (username, email, hashed_password, role, bank_id, branch_id, is_active)
            VALUES ('hdfc_user', 'hdfc@fiducia.local', :pw, 'branch_user', :bank_id, :branch_id, true)
        """), {"pw": hashed_pw, "bank_id": bank_id, "branch_id": branch_id})
        conn.commit()
        print("Created hdfc_user with branch assignment")
    else:
        user_id, username, branch_id = user
        print(f"Found hdfc_user: id={user_id}, branch_id={branch_id}")
        
        if not branch_id:
            print("User has no branch - assigning one...")
            # Get HDFC bank
            bank_result = conn.execute(text("SELECT id FROM banks WHERE code = 'HDFC'"))
            bank = bank_result.fetchone()
            if not bank:
                conn.execute(text("INSERT INTO banks (name, code, ifsc_prefix, is_active) VALUES ('HDFC Bank', 'HDFC', 'HDFC', true)"))
                conn.commit()
                bank_result = conn.execute(text("SELECT id FROM banks WHERE code = 'HDFC'"))
                bank = bank_result.fetchone()
            bank_id = bank[0]
            
            # Get or create branch
            branch_result = conn.execute(text("SELECT id FROM branches WHERE bank_id = :bank_id"), {"bank_id": bank_id})
            branch = branch_result.fetchone()
            if not branch:
                conn.execute(text("""
                    INSERT INTO branches (bank_id, branch_code, branch_name, ifsc_code, demo_access, is_active) 
                    VALUES (:bank_id, 'HDFC001', 'HDFC Main Branch', 'HDFC0000001', true, true)
                """), {"bank_id": bank_id})
                conn.commit()
                branch_result = conn.execute(text("SELECT id FROM branches WHERE bank_id = :bank_id"), {"bank_id": bank_id})
                branch = branch_result.fetchone()
            branch_id = branch[0]
            
            # Assign branch to user
            conn.execute(text("UPDATE users SET branch_id = :branch_id, bank_id = :bank_id WHERE id = :user_id"),
                        {"branch_id": branch_id, "bank_id": bank_id, "user_id": user_id})
            conn.commit()
            print(f"Assigned branch {branch_id} to hdfc_user")
        else:
            # Check if branch has demo_access
            demo_result = conn.execute(text("SELECT demo_access FROM branches WHERE id = :branch_id"), {"branch_id": branch_id})
            demo = demo_result.fetchone()
            if demo and not demo[0]:
                conn.execute(text("UPDATE branches SET demo_access = true WHERE id = :branch_id"), {"branch_id": branch_id})
                conn.commit()
                print(f"Enabled demo_access for branch {branch_id}")
            else:
                print(f"Branch {branch_id} already has demo_access enabled")
    
    print("\nFix complete! Logout and login again as hdfc_user.")
