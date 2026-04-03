from app.core.config import settings
from sqlalchemy import create_engine, text

e = create_engine(settings.DATABASE_URL)
with e.connect() as c:
    r = c.execute(text('SELECT id, username, email, bank_id FROM users ORDER BY id'))
    rows = r.fetchall()
    print(f'Total users: {len(rows)}')
    for row in rows[:15]:
        print(f'  ID:{row[0]} | {row[1]} | Bank:{row[3]}')
    
    # Check yes_user specifically
    r2 = c.execute(text("SELECT id, username, hashed_password FROM users WHERE username='yes_user'"))
    yes_user = r2.fetchone()
    if yes_user:
        print(f'\nyes_user found: ID={yes_user[0]}')
        print(f'Hashed password: {yes_user[2][:50]}...')
    else:
        print('\nyes_user NOT FOUND in database!')
