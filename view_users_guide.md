# 👥 SafeStream Admin User Management Guide

## Overview
In SafeStream, there are no separate admin roles - **any authenticated user can perform admin actions**. This guide shows you all the ways to view and manage users in your system.

## Method 1: Using the List Users Script (Recommended)

```bash
python3 list_users.py
```

**Output includes:**
- Username, email, user ID
- Account status (active/inactive) 
- Creation and last update timestamps
- Recent admin actions performed by each user

## Method 2: Direct Database Query

```bash
python3 -c "
import asyncio
from app.db import async_session, init_db

async def quick_user_list():
    await init_db()
    async with async_session() as session:
        from sqlalchemy import select
        from app.db.models import User
        
        stmt = select(User).order_by(User.username)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        print(f'Total users: {len(users)}')
        for user in users:
            status = '🟢' if user.is_active else '🔴'
            print(f'{status} {user.username} ({user.email})')

asyncio.run(quick_user_list())
"
```

## Method 3: Via API (if server is running)

### Get User Count
```bash
curl -X GET "http://localhost:8000/api/users/count"
```

### List All Users (requires admin auth)
```bash
# First get auth token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_ADMIN_USERNAME&password=YOUR_PASSWORD" \
  | jq -r '.access_token')

# Then list users
curl -X GET "http://localhost:8000/api/users" \
  -H "Authorization: Bearer $TOKEN"
```

## Method 4: From Dashboard

1. Start the dashboard: `streamlit run dashboard/app.py`
2. Login with any user credentials
3. User list available in the admin section

## Method 5: SQLite Direct Query (Advanced)

```bash
sqlite3 data/safestream.db "SELECT username, email, is_active, created_at FROM users ORDER BY created_at DESC;"
```

## User Management Commands

### Create New Admin User
```bash
python3 create_admin_user.py
```

### Delete User (via script)
```bash
python3 -c "
import asyncio
from app.db import async_session, init_db
from app.services import database as db_service

async def delete_user_by_username():
    username = input('Enter username to delete: ')
    await init_db()
    
    async with async_session() as session:
        user = await db_service.get_user_by_username(session, username)
        if user:
            await db_service.delete_user(session, user.id)
            print(f'✅ Deleted user: {username}')
        else:
            print(f'❌ User not found: {username}')

asyncio.run(delete_user_by_username())
"
```

## Important Notes

1. **No Role Separation**: All users have equal admin capabilities when authenticated
2. **Password Security**: All passwords are bcrypt hashed
3. **JWT Tokens**: Dashboard authentication uses JWT with 30-minute expiration
4. **Database Storage**: All user data stored in SQLite database (`data/safestream.db`)

## Troubleshooting

**No users found?**
```bash
python3 create_admin_user.py
```

**Can't authenticate?**
- Check username/password are correct
- Verify user is active: `python3 list_users.py`
- Try creating new admin user

**Database issues?**
```bash
# Check database exists
ls -la data/safestream.db

# Reset database (WARNING: deletes all data)
rm data/safestream.db
python3 -c "from app.db import init_db; import asyncio; asyncio.run(init_db())"
``` 