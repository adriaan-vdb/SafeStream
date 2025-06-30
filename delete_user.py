#!/usr/bin/env python3
"""
Script to delete users from the SafeStream database.

This script provides a safe way to remove admin users with confirmation
prompts and detailed feedback about what will be deleted.
"""

import asyncio
import sys

from app.db import async_session, init_db
from app.services import database as db_service


async def delete_user_interactive():
    """Interactively delete a user with confirmation."""
    print("🗑️  SafeStream User Deletion Tool")
    print("=" * 50)

    # Initialize database
    await init_db()

    async with async_session() as session:
        # First, show all users
        from sqlalchemy import select

        from app.db.models import AdminAction, GiftEvent, Message, User

        stmt = select(User).order_by(User.username)
        result = await session.execute(stmt)
        users = result.scalars().all()

        if not users:
            print("📭 No users found in database")
            return

        print(f"📊 Current users ({len(users)}):")
        for i, user in enumerate(users, 1):
            status = "🟢" if user.is_active else "🔴"
            print(f"  {i}. {status} {user.username} ({user.email})")

        print("\n" + "=" * 50)

        # Get username to delete
        while True:
            username = input("\n👤 Enter username to delete (or 'q' to quit): ").strip()

            if username.lower() == "q":
                print("❌ Operation cancelled")
                return

            if not username:
                print("❌ Username cannot be empty")
                continue

            # Find the user
            target_user = await db_service.get_user_by_username(session, username)
            if target_user:
                break
            else:
                print(f"❌ User '{username}' not found")
                continue

        # Show what will be deleted
        print(f"\n⚠️  USER DELETION PREVIEW for '{target_user.username}':")
        print("=" * 60)
        print(f"👤 Username: {target_user.username}")
        print(f"📧 Email: {target_user.email}")
        print(f"🆔 ID: {target_user.id}")
        print(f"📅 Created: {target_user.created_at}")

        # Count related data that will be deleted
        from sqlalchemy import func

        message_count = (
            await session.scalar(
                select(func.count(Message.id)).where(Message.user_id == target_user.id)
            )
            or 0
        )
        gift_count = (
            await session.scalar(
                select(func.count(GiftEvent.id)).where(
                    GiftEvent.from_user_id == target_user.id
                )
            )
            or 0
        )
        admin_action_count = (
            await session.scalar(
                select(func.count(AdminAction.id)).where(
                    AdminAction.admin_user_id == target_user.id
                )
            )
            or 0
        )
        targeted_action_count = (
            await session.scalar(
                select(func.count(AdminAction.id)).where(
                    AdminAction.target_user_id == target_user.id
                )
            )
            or 0
        )

        print("\n📊 RELATED DATA TO BE DELETED:")
        print(f"  💬 Messages: {message_count}")
        print(f"  🎁 Gifts sent: {gift_count}")
        print(f"  🛡️  Admin actions performed: {admin_action_count}")
        print(f"  🎯 Times targeted by admin actions: {targeted_action_count}")

        # Confirmation prompts
        print("\n⚠️  WARNING: This action cannot be undone!")
        print("All user data and related records will be permanently deleted.")

        confirm1 = (
            input(
                f"\n❓ Are you sure you want to delete '{target_user.username}'? (yes/no): "
            )
            .strip()
            .lower()
        )
        if confirm1 != "yes":
            print("❌ Operation cancelled")
            return

        confirm2 = input(
            f"❓ Type the username '{target_user.username}' to confirm: "
        ).strip()
        if confirm2 != target_user.username:
            print("❌ Username confirmation failed. Operation cancelled")
            return

        # Perform deletion
        print(f"\n🗑️  Deleting user '{target_user.username}'...")

        success = await db_service.delete_user(session, target_user.id)

        if success:
            print("✅ User successfully deleted!")
            print(f"   👤 Deleted user: {target_user.username}")
            print(f"   💬 Deleted {message_count} messages")
            print(f"   🎁 Deleted {gift_count} gift events")
            print(f"   🛡️  Deleted {admin_action_count} admin actions")
        else:
            print("❌ Failed to delete user")


async def delete_user_by_name(username: str):
    """Delete a user by username (for scripting)."""
    await init_db()

    async with async_session() as session:
        user = await db_service.get_user_by_username(session, username)
        if not user:
            print(f"❌ User '{username}' not found")
            return False

        success = await db_service.delete_user(session, user.id)
        if success:
            print(f"✅ Deleted user: {username}")
            return True
        else:
            print(f"❌ Failed to delete user: {username}")
            return False


async def delete_all_users():
    """Delete all users (dangerous - requires confirmation)."""
    print("🚨 DELETE ALL USERS - DANGER ZONE")
    print("=" * 50)

    await init_db()

    async with async_session() as session:
        from sqlalchemy import select

        from app.db.models import User

        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()

        if not users:
            print("📭 No users to delete")
            return

        print(f"⚠️  This will delete ALL {len(users)} users:")
        for user in users:
            print(f"  - {user.username} ({user.email})")

        print("\n🚨 WARNING: This will permanently delete ALL user data!")
        print("This includes all messages, gifts, admin actions, and user accounts.")

        confirm = input("\n❓ Type 'DELETE ALL USERS' to confirm: ").strip()
        if confirm != "DELETE ALL USERS":
            print("❌ Operation cancelled")
            return

        print(f"\n🗑️  Deleting all {len(users)} users...")
        deleted_count = 0

        for user in users:
            success = await db_service.delete_user(session, user.id)
            if success:
                deleted_count += 1
                print(f"✅ Deleted: {user.username}")

        print(f"\n🧹 Cleanup complete: {deleted_count}/{len(users)} users deleted")


async def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) == 1:
        # Interactive mode
        await delete_user_interactive()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--delete-all":
            await delete_all_users()
        elif sys.argv[1] in ["--help", "-h", "help"]:
            print("Usage:")
            print("  python3 delete_user.py                    # Interactive mode")
            print("  python3 delete_user.py <username>         # Delete specific user")
            print("  python3 delete_user.py --delete-all       # Delete all users")
            print("  python3 delete_user.py --help             # Show this help")
        else:
            # Delete specific user
            username = sys.argv[1]
            await delete_user_by_name(username)
    else:
        print("Usage:")
        print("  python3 delete_user.py                    # Interactive mode")
        print("  python3 delete_user.py <username>         # Delete specific user")
        print("  python3 delete_user.py --delete-all       # Delete all users")


if __name__ == "__main__":
    asyncio.run(main())
