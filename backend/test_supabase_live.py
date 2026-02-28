import asyncio
import httpx
from supabase import create_client, Client

url = "https://fbkwtmcefddxpdrvxqki.supabase.co"
key = "sb_publishable_uCWMUWM-1n8MHIgtYBieVA_ZQrAITOI"
supabase: Client = create_client(url, key)


async def run_integration_tests():
    email = "integration_tester@ufl.edu"
    password = "SuperSecretPassword123!"

    # 1. Sign up/In to get a real JWT
    print("\n--- 1. Authenticating with Supabase ---")
    try:
        # We rely on the user having confirmed an email or email confirmations being off
        # If it fails, we will try to sign in
        res = supabase.auth.sign_up({"email": email, "password": password})
        # Note: If email confirmations are enabled, sign_up will not return a session
        session = res.session
        print("Signed up successfully.")
    except Exception:
        print("Sign up failed (may already exist).")
        session = None

    if not session:
        try:
            print("Attempting sign in...")
            res = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            session = res.session
            print("Signed in successfully.")
        except Exception as e2:
            print("Sign in failed:", e2)
            return

    if not session:
        print("No active session returned (Check if email confirmation is required).")
        print("Cannot test authenticated endpoints without a confirmed user.")
        print(
            "We will skip B3 and B4. We need the user to either confirm the email or provide a working account."
        )
        # We can still test B5 and B6 if we know a user ID. Let's try to query the users table for any user?
        # Actually without auth, we can't list users easily unless we have an ID.
        return

    access_token = session.access_token
    user_id = session.user.id
    print(f"Acquired JWT for User ID: {user_id}")

    # Run the tests against the local server, passing the real JWT
    # Assumes the backend is running on port 8000 via docker-compose
    base_url = "http://127.0.0.1:8000/api/v1"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
        # Test B3: GET /users/me
        print("\n--- Testing GET /users/me ---")
        try:
            response = await client.get("/users/me")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Request failed: {e}")

        # Test B4: PATCH /users/me
        print("\n--- Testing PATCH /users/me ---")
        try:
            payload = {
                "full_name": "Integration Tester",
                "profile_picture_url": "https://example.com/avatar.png",
            }
            response = await client.patch("/users/me", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Request failed: {e}")

        # Test B5: GET /users/{user_id}
        print(f"\n--- Testing GET /users/{user_id} ---")
        try:
            # We must use a separate client without auth to test public access
            async with httpx.AsyncClient(base_url=base_url) as public_client:
                response = await public_client.get(f"/users/{user_id}")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Request failed: {e}")

        # Test B6: GET /users/{user_id}/projects
        print(f"\n--- Testing GET /users/{user_id}/projects ---")
        try:
            response = await client.get(f"/users/{user_id}/projects")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Request failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
