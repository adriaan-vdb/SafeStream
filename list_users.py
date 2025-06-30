#!/usr/bin/env python3
"""
Script to list all users in the SafeStream database.

This script shows all registered users who can potentially access
the admin dashboard (any authenticated user has admin capabilities).
"""

import asyncio

from app.db import async_session, init_db


async def list_all_users():
    """List all users in the database with their details."""
    print("👥 SafeStream User List")
    print("=" * 50)

    # Initialize database connection
    await init_db()

    async with async_session() as session:
        # Get all users
        from sqlalchemy import select

        from app.db.models import User

        stmt = select(User).order_by(User.created_at.desc())
        result = await session.execute(stmt)
        users = result.scalars().all()

        if not users:
            print("📭 No users found in database")
            print("\n💡 Create an admin user with: python create_admin_user.py")
            return

        print(f"📊 Total users: {len(users)}")
        print("\n" + "=" * 80)

        for i, user in enumerate(users, 1):
            status = "🟢 Active" if user.is_active else "🔴 Inactive"
            created = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
            updated = user.updated_at.strftime("%Y-%m-%d %H:%M:%S")

            print(f"{i:2d}. {user.username}")
            print(f"    📧 Email: {user.email}")
            print(f"    🆔 ID: {user.id}")
            print(f"    {status}")
            print(f"    📅 Created: {created}")
            print(f"    🔄 Updated: {updated}")

            # Check for recent activity (admin actions)
            from app.db.models import AdminAction

            stmt_actions = (
                select(AdminAction).where(AdminAction.admin_user_id == user.id).limit(3)
            )
            result_actions = await session.execute(stmt_actions)
            recent_actions = result_actions.scalars().all()

            if recent_actions:
                print(f"    🎯 Recent Admin Actions ({len(recent_actions)}):")
                for action in recent_actions:
                    action_time = action.timestamp.strftime("%m-%d %H:%M")
                    print(f"       • {action.action} at {action_time}")

            print("-" * 80)

        print(f"\n💡 Any of these {len(users)} users can login to the admin dashboard")
        print("🚀 Dashboard: streamlit run dashboard/app.py")


if __name__ == "__main__":
    asyncio.run(list_all_users())
