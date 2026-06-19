from uuid import uuid4

from fastapi.testclient import TestClient
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[0]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
import db


def _register_and_login(client: TestClient, username: str, password: str = "testpassword123") -> None:
    response = client.post("/register", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 200, response.text


def test_register_habit_to_my_habits():
    with TestClient(app) as client:
        username = f"user-{uuid4()}"
        _register_and_login(client, username)

        # Create a habit for this user in the "Health" category so the test
        # does not depend on globally seeded data (which is now scoped to
        # the demo user).
        response = client.post(
            "/habits",
            json={"name": "Drink Water", "description": "Stay hydrated.", "category": "Health"},
        )
        assert response.status_code == 201, response.text

        # First, find a habit that is not in "My Habits"
        response = client.get("/habits/Health")
        assert response.status_code == 200
        health_habits = response.json()
        assert len(health_habits) > 0
        habit_to_register = health_habits[0]
        habit_id = habit_to_register["id"]

        # Register it
        response = client.post(f"/ui/page2/register-habit?category=Health", data={"habit_id": habit_id})
        assert response.status_code == 200
        assert 'id="my-habits-section"' in response.text
        assert 'hx-swap-oob="true"' in response.text
        assert 'id="page2-category-picker"' in response.text
        assert habit_to_register["name"] in response.text

        # Verify it's now in My Habits
        response = client.get("/habits/My Habits")
        assert response.status_code == 200
        my_habits = response.json()
        assert any(h["id"] == habit_id for h in my_habits)

def test_register_original_habit_to_my_habits():
    with TestClient(app) as client:
        username = f"user-{uuid4()}"
        _register_and_login(client, username)

        habit_name = "Original Test Habit"
        habit_description = "A brand-new habit created from the Original tab."

        response = client.post(
            "/ui/page2/register-original-habit?category=Original",
            data={"name": habit_name, "description": habit_description},
        )
        assert response.status_code == 200
        assert 'id="my-habits-section"' in response.text
        assert 'hx-swap-oob="true"' in response.text
        assert 'id="page2-category-picker"' in response.text
        assert habit_name in response.text

        # Verify it's now in My Habits
        response = client.get("/habits/My Habits")
        assert response.status_code == 200
        my_habits = response.json()
        assert any(h["name"] == habit_name and h["category"] == "My Habits" for h in my_habits)


def test_user_cannot_see_other_users_habits_and_unauthenticated_is_rejected():
    with TestClient(app) as client_a, TestClient(app) as client_b:
        username_a = f"user-a-{uuid4()}"
        username_b = f"user-b-{uuid4()}"
        _register_and_login(client_a, username_a)
        _register_and_login(client_b, username_b)

        # User A creates a habit.
        response = client_a.post(
            "/habits",
            json={"name": "A's Secret Habit", "description": "private", "category": "Original"},
        )
        assert response.status_code == 201, response.text
        created_habit_id = response.json()["id"]

        # User B cannot see user A's habit.
        response = client_b.get("/habits")
        assert response.status_code == 200
        b_habit_ids = {h["id"] for h in response.json()}
        assert created_habit_id not in b_habit_ids

        # Unauthenticated request is rejected.
        with TestClient(app) as anon_client:
            response = anon_client.get("/habits")
            assert response.status_code == 401


def test_user_cannot_update_or_delete_other_users_habit_via_ui_routes():
    with TestClient(app) as client_a, TestClient(app) as client_b:
        username_a = f"user-a-{uuid4()}"
        username_b = f"user-b-{uuid4()}"
        _register_and_login(client_a, username_a)
        _register_and_login(client_b, username_b)

        # User A creates a habit.
        response = client_a.post(
            "/habits",
            json={"name": "A's Other Habit", "description": "private", "category": "Original"},
        )
        assert response.status_code == 201, response.text
        created_habit_id = response.json()["id"]

        # User B attempts to update user A's habit via the UI route: should be 404, not 500.
        response = client_b.put(
            f"/ui/habits/{created_habit_id}",
            json={
                "id": created_habit_id,
                "name": "Hijacked",
                "description": "hijacked",
                "category": "Original",
            },
        )
        assert response.status_code == 404, response.text

        # User B attempts to delete user A's habit via the UI route: should be 404, not 500.
        response = client_b.delete(f"/ui/habits/{created_habit_id}")
        assert response.status_code == 404, response.text

        # User A's habit is untouched and still belongs to user A.
        response = client_a.get("/habits")
        assert response.status_code == 200
        a_habits = {h["id"]: h for h in response.json()}
        assert created_habit_id in a_habits
        assert a_habits[created_habit_id]["name"] == "A's Other Habit"


if __name__ == "__main__":
    import asyncio
    # Initialize DB for testing
    async def run_init():
        await db.init_db(seed_sample=True, reset=True)
    asyncio.run(run_init())

    test_register_habit_to_my_habits()
    print("Test passed!")
