#!/usr/bin/env python3
"""
Authentication test script for SafeStream.

This script helps debug login issues by testing authentication
against the FastAPI backend directly.
"""

import requests


def test_authentication(username: str, password: str):
    """Test authentication for a given username/password."""
    print(f"🔍 Testing authentication for: {username}")
    print("=" * 50)

    try:
        # Test authentication
        print("1️⃣ Attempting login...")
        response = requests.post(
            "http://localhost:8000/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )

        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")

        if response.ok:
            data = response.json()
            token = data.get("access_token")
            token_type = data.get("token_type", "bearer")

            print("✅ Login successful!")
            print(f"   Token Type: {token_type}")
            print(f"   Token: {token[:20]}...{token[-10:] if token else 'None'}")

            # Test token with protected endpoint
            print("\n2️⃣ Testing token with protected endpoint...")
            test_response = requests.get(
                "http://localhost:8000/api/mod/threshold",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            print(f"   Status Code: {test_response.status_code}")
            print(f"   Response: {test_response.text}")

            if test_response.ok:
                print("✅ Token validation successful!")
                return True, token
            else:
                print("❌ Token validation failed!")
                return False, None
        else:
            print("❌ Login failed!")
            if response.status_code == 401:
                print("   Reason: Invalid credentials")
            elif response.status_code == 422:
                print("   Reason: Invalid request format")
            else:
                print(f"   Reason: HTTP {response.status_code}")
            return False, None

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the FastAPI server running on port 8000?")
        print("   Start it with: uvicorn app.main:app --reload")
        return False, None
    except requests.exceptions.Timeout:
        print("❌ Timeout: Server took too long to respond")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None


def main():
    """Main function to test authentication."""
    print("🔐 SafeStream Authentication Tester")
    print("=" * 50)

    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        health_response = requests.get("http://localhost:8000/healthz", timeout=3)
        if health_response.ok:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server responded with status: {health_response.status_code}")
    except Exception:
        print("❌ Server is not running. Start it with: uvicorn app.main:app --reload")
        return

    print("\n" + "=" * 50)

    # Test known users
    test_users = [
        ("admin", "admin"),
        ("admin2", "admin2"),
        ("test_streamer", "test_streamer"),
    ]

    for username, password in test_users:
        print(f"\n🧪 Testing {username}...")
        success, token = test_authentication(username, password)
        if success:
            print(f"✅ {username} can login successfully!")
        else:
            print(f"❌ {username} login failed")
        print("-" * 30)

    # Interactive test
    print("\n🎯 Interactive Test")
    print("=" * 30)
    username = input("Enter username to test: ").strip()
    password = input("Enter password: ").strip()

    if username and password:
        success, token = test_authentication(username, password)
        if success:
            print("\n🎉 SUCCESS! You can use these credentials in the dashboard:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print("   Dashboard: http://localhost:8501")
        else:
            print("\n💡 TIPS:")
            print("   1. Make sure the username exists: python3 list_users.py")
            print("   2. Create a new user: python3 create_admin_user.py")
            print("   3. Check server logs for errors")


if __name__ == "__main__":
    main()
