#!/usr/bin/env python3
"""
Script to create an admin user for SafeStream dashboard testing.

Run this script to create a test admin user that can be used to login
to the Streamlit moderator dashboard.
"""

import asyncio
import getpass

from passlib.context import CryptContext

from app.db import async_session, init_db
from app.services import database as db_service

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


async def create_admin_user():
    """Create an admin user interactively."""
    print("🔧 SafeStream Admin User Creator")
    print("=" * 40)

    # Get admin credentials
    username = input("Enter admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return

    email = input("Enter admin email: ").strip()
    if not email:
        email = f"{username}@safestream.admin"
        print(f"📧 Using default email: {email}")

    password = getpass.getpass("Enter admin password: ")
    if not password:
        print("❌ Password cannot be empty")
        return

    password_confirm = getpass.getpass("Confirm admin password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        return

    # Initialize database
    print("\n🔄 Initializing database connection...")
    await init_db()

    async with async_session() as session:
        # Check if user already exists
        existing_user = await db_service.get_user_by_username(session, username)
        if existing_user:
            print(f"❌ User '{username}' already exists")
            return

        # Hash password and create user
        hashed_password = hash_password(password)

        try:
            user = await db_service.create_user(
                session, username, email, hashed_password
            )
            print("\n✅ Admin user created successfully!")
            print(f"📋 Username: {user.username}")
            print(f"📧 Email: {user.email}")
            print(f"🆔 User ID: {user.id}")
            print(f"📅 Created: {user.created_at}")

            print("\n🎯 You can now use these credentials to login to the dashboard:")
            print(f"   Username: {username}")
            print("   Password: [hidden]")

            print("\n🚀 Start the dashboard with: streamlit run dashboard/app.py")

        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")


async def main():
    """Main function."""
    try:
        await create_admin_user()
    except KeyboardInterrupt:
        print("\n❌ User creation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
