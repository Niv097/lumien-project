from app.core.config import settings
from sqlalchemy import create_engine, text

e = create_engine(settings.DATABASE_URL)

with e.connect() as c:
    # Show current users
    r = c.execute(text('SELECT id, username FROM users'))
    print("Current users:")
    for row in r:
        print(f"  {row[0]}: {row[1]}")
    
    # Delete wrong users (1_user, 2_user, etc.)
    c.execute(text("DELETE FROM user_roles WHERE user_id IN (SELECT id FROM users WHERE username LIKE '_user' AND username NOT LIKE '%_%')"))
    c.execute(text("DELETE FROM users WHERE username LIKE '_user' AND username NOT LIKE '%_%'"))
    c.commit()
    print("\nDeleted invalid users")
    
    # Show remaining users
    r = c.execute(text('SELECT id, username FROM users'))
    print("\nRemaining users:")
    for row in r:
        print(f"  {row[0]}: {row[1]}")
