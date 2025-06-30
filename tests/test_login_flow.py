#!/usr/bin/env python3
"""
Test script to verify the login flow works correctly after the session fix.

This script tests that users can login multiple times without being blocked,
simulating the browser refresh scenario.
"""

import time

import requests


def test_login_flow():
    """Test the complete login flow including multiple logins."""
    print("🔄 Testing Login Flow - Session Replacement")
    print("=" * 50)

    base_url = "http://localhost:8000"
    username = "admin"
    password = "admin"

    # Test multiple successive logins
    for i in range(3):
        print(f"\n🔐 Login Attempt #{i+1}")
        print("-" * 30)

        try:
            # Simulate login
            response = requests.post(
                f"{base_url}/auth/login",
                data={"username": username, "password": password},
                timeout=5,
            )

            print(f"Status: {response.status_code}")

            if response.ok:
                data = response.json()
                token = data.get("access_token", "")
                print(f"✅ Login #{i+1} successful!")
                print(f"Token: {token[:30]}...")

                # Test the token works
                test_response = requests.get(
                    f"{base_url}/api/mod/threshold",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=3,
                )

                if test_response.ok:
                    print("✅ Token validation successful")
                else:
                    print(f"❌ Token validation failed: {test_response.status_code}")

            else:
                print(f"❌ Login #{i+1} failed!")
                data = response.json()
                print(f"Error: {data.get('detail', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

        # Small delay between attempts
        if i < 2:
            time.sleep(1)

    print("\n🎯 Summary:")
    print("If all 3 login attempts succeeded, session replacement is working!")
    print("You can now refresh your browser and login again without issues.")


def test_dashboard_scenario():
    """Test the specific dashboard scenario."""
    print("\n📊 Testing Dashboard Scenario")
    print("=" * 40)

    # This simulates what happens when you:
    # 1. Login to dashboard
    # 2. Refresh browser (lose session state)
    # 3. Try to login again

    base_url = "http://localhost:8000"
    username = "admin"
    password = "admin"

    print("1️⃣ Initial dashboard login...")
    response1 = requests.post(
        f"{base_url}/auth/login",
        data={"username": username, "password": password},
        timeout=5,
    )

    if response1.ok:
        token1 = response1.json().get("access_token")
        print(f"✅ Initial login successful: {token1[:20]}...")
    else:
        print(f"❌ Initial login failed: {response1.status_code}")
        return

    print("\n2️⃣ Simulating browser refresh...")
    print("   (In real usage, you'd refresh the browser here)")
    time.sleep(2)

    print("\n3️⃣ Attempting login again (after 'refresh')...")
    response2 = requests.post(
        f"{base_url}/auth/login",
        data={"username": username, "password": password},
        timeout=5,
    )

    if response2.ok:
        token2 = response2.json().get("access_token")
        print(f"✅ Second login successful: {token2[:20]}...")
        print("🎉 Perfect! You can now login again after browser refresh!")

        # Verify tokens are different (new session)
        if token1 != token2:
            print("✅ New session created (tokens are different)")
        else:
            print("⚠️  Same token returned (unexpected)")

    else:
        print(f"❌ Second login failed: {response2.status_code}")
        error_data = response2.json()
        print(f"Error: {error_data.get('detail', 'Unknown error')}")


if __name__ == "__main__":
    print("🧪 SafeStream Login Flow Test")
    print("=" * 50)

    # Check server is running
    try:
        health = requests.get("http://localhost:8000/healthz", timeout=3)
        if health.ok:
            print("✅ Server is running")
        else:
            print(f"⚠️ Server health check failed: {health.status_code}")
    except Exception:
        print("❌ Server is not running. Start with: uvicorn app.main:app --reload")
        exit(1)

    # Run tests
    test_login_flow()
    test_dashboard_scenario()

    print("\n🎯 Next Steps:")
    print("1. Open dashboard: streamlit run dashboard/app.py")
    print("2. Login with: admin / admin")
    print("3. Refresh the page multiple times")
    print("4. Try logging in again - should work immediately!")
