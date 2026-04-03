#!/usr/bin/env python3
"""Fix hdfc_user branch assignment and demo access"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:password@localhost:5432/fiducia_saas')
Session = sessionmaker(bind=engine)
s = Session()

from app.models.models import User, Branch, Bank
from app.core.security import get_password_hash

# Get HDFC bank
hdfc = s.query(Bank).filter(Bank.code == 'HDFC').first()
if not hdfc:
    print('Creating HDFC bank...')
    hdfc = Bank(name='HDFC Bank', code='HDFC', ifsc_prefix='HDFC')
    s.add(hdfc)
    s.commit()
    s.refresh(hdfc)
print(f'HDFC Bank ID: {hdfc.id}')

# Get or create HDFC branch
branch = s.query(Branch).filter(Branch.bank_id == hdfc.id).first()
if not branch:
    print('Creating HDFC branch...')
    branch = Branch(
        bank_id=hdfc.id,
        branch_code='HDFC001',
        branch_name='HDFC Main Branch',
        ifsc_code='HDFC0000001',
        demo_access=True
    )
    s.add(branch)
    s.commit()
    s.refresh(branch)
print(f'HDFC Branch ID: {branch.id}, Name: {branch.branch_name}')

# Enable demo access
if not branch.demo_access:
    branch.demo_access = True
    s.commit()
    print('Demo access enabled')

# Get or create hdfc_user
user = s.query(User).filter(User.username == 'hdfc_user').first()
if user:
    user.branch_id = branch.id
    user.bank_id = hdfc.id
    s.commit()
    print(f'Updated hdfc_user: branch_id={branch.id}')
else:
    user = User(
        username='hdfc_user',
        email='hdfc@fiducia.local',
        hashed_password=get_password_hash('hdfc123'),
        role='branch_user',
        bank_id=hdfc.id,
        branch_id=branch.id,
        is_active=True
    )
    s.add(user)
    s.commit()
    print(f'Created hdfc_user with branch_id={branch.id}')

s.close()
print('Done! Refresh the page and try again.')
