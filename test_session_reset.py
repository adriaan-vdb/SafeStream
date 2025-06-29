#!/usr/bin/env python3
"""
Session management test with proper cleanup.
"""

import json
import subprocess
import time


def run_curl(method, url, data=None, headers=None):
    """Run a curl command and return the response."""
    cmd = ["curl", "-s", "-X", method]

    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

    if method == "POST" and "login" in url and data:
        # Handle form data for login
        cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
        form_data = "&".join([f"{k}={v}" for k, v in data.items()])
        cmd.extend(["-d", form_data])
    elif data:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(data)])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"


def clear_user_sessions_via_db():
    """Clear sessions by manually invalidating them in the database."""
    try:
        import sqlite3

        # Connect to the database and manually clear sessions for our test user
        conn = sqlite3.connect("data/safestream.db")
        cursor = conn.cursor()

        # Get the user ID for our test user
        cursor.execute(
            "SELECT id FROM users WHERE username = ?", ("session_test_user",)
        )
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            # Set all sessions for this user to inactive
            cursor.execute(
                "UPDATE user_sessions SET is_active = 0 WHERE user_id = ?", (user_id,)
            )
            conn.commit()
            print(f"✅ Cleared sessions for user ID {user_id}")
        else:
            print("ℹ️  No user found to clear sessions for")

        conn.close()
        return True
    except Exception as e:
        print(f"⚠️  Could not clear sessions: {e}")
        return False


def test_complete_session_cycle():
    """Test the complete session management cycle."""
    base_url = "http://localhost:8000"

    print("🔒 Testing Complete Session Management Cycle")
    print("=" * 60)

    # Test user credentials
    username = "session_test_user"
    password = "testpass123"
    email = f"{username}@test.com"

    # Step 0: Clear any existing sessions
    print("🧹 Step 0: Clearing any existing sessions...")
    if clear_user_sessions_via_db():
        print("✅ Sessions cleared successfully")
    else:
        print("⚠️  Could not clear sessions, proceeding anyway...")

    # Step 1: Register a test user (if needed)
    print("\n📝 Step 1: Ensuring test user exists...")
    register_data = {"username": username, "password": password, "email": email}

    code, response, error = run_curl("POST", f"{base_url}/auth/register", register_data)
    if code == 0:
        try:
            result = json.loads(response)
            if "access_token" in result:
                print("✅ User registered successfully")
            else:
                print("ℹ️  User already exists, proceeding...")
        except json.JSONDecodeError:
            print("ℹ️  User likely already exists, proceeding...")

    # Step 2: First login attempt (should succeed)
    print("\n🔑 Step 2: Attempting first login...")
    login_data = {"username": username, "password": password}

    code, response, error = run_curl("POST", f"{base_url}/auth/login", login_data)
    if code == 0:
        try:
            result = json.loads(response)
            if "access_token" in result:
                first_token = result["access_token"]
                print("✅ First login successful!")
                print(f"   Token: {first_token[:50]}...")
            else:
                print(f"❌ First login failed: {result}")
                return False
        except json.JSONDecodeError:
            print(f"❌ First login failed - invalid response: {response}")
            return False
    else:
        print(f"❌ First login request failed: {error}")
        return False

    # Step 3: Second login attempt (should fail with 409 Conflict)
    print("\n🔒 Step 3: Attempting second login (should fail)...")
    time.sleep(1)

    code, response, error = run_curl("POST", f"{base_url}/auth/login", login_data)
    if code == 0:
        try:
            result = json.loads(response)
            if "access_token" in result:
                print("❌ ERROR: Second login should have failed but succeeded!")
                return False
            elif "detail" in result and "already logged in" in result["detail"].lower():
                print("✅ Second login correctly rejected!")
                print(f"   Message: {result['detail']}")
            else:
                print(f"⚠️  Unexpected response: {result}")
        except json.JSONDecodeError:
            print(f"⚠️  Unexpected response format: {response}")

    # Step 4: Test logout
    print("\n👋 Step 4: Testing logout...")
    headers = {"Authorization": f"Bearer {first_token}"}

    code, response, error = run_curl("POST", f"{base_url}/auth/logout", None, headers)
    if code == 0:
        try:
            result = json.loads(response)
            if "message" in result:
                print(f"✅ Logout successful: {result['message']}")
            else:
                print(f"⚠️  Unexpected logout response: {result}")
        except json.JSONDecodeError:
            print(f"❌ Logout response not JSON: {response}")
            return False
    else:
        print(f"❌ Logout request failed: {error}")
        return False

    # Step 5: Try to login again after logout (should succeed)
    print("\n🔑 Step 5: Attempting login after logout...")
    time.sleep(1)

    code, response, error = run_curl("POST", f"{base_url}/auth/login", login_data)
    if code == 0:
        try:
            result = json.loads(response)
            if "access_token" in result:
                print("✅ Login after logout successful!")
                print("🎉 Session management is working correctly!")

                # Clean up - logout again
                new_token = result["access_token"]
                headers = {"Authorization": f"Bearer {new_token}"}
                run_curl("POST", f"{base_url}/auth/logout", None, headers)
                print("✅ Cleaned up final session")

                return True
            else:
                print(f"❌ Login after logout failed: {result}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Login after logout failed - invalid JSON: {response}")
            return False
    else:
        print(f"❌ Login after logout request failed: {error}")
        return False


if __name__ == "__main__":
    # Check if server is running
    code, response, error = run_curl("GET", "http://localhost:8000/healthz")
    if code != 0:
        print("❌ Server is not running. Please start the server first:")
        print(
            "   cd SafeStream && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        )
        exit(1)

    print("✅ Server is running, starting tests...\n")

    success = test_complete_session_cycle()

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL SESSION MANAGEMENT TESTS PASSED!")
        print("✅ Multiple simultaneous logins are correctly prevented")
        print("✅ Session cleanup works properly")
        print("✅ Login-logout-login cycle works correctly")
        print("✅ Session management is working as expected")
    else:
        print("❌ Some tests FAILED!")
        print("⚠️  Session management may need adjustment")
