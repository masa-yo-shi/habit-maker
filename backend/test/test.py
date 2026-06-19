import os
from fastapi.testclient import TestClient
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "test-secret")
COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "access_token")

from main import app

def ensure_user(client: TestClient, username: str, password:str) -> None:
    response = client.post(
        "/register", data={"username": username, "password": password}
    )
    if response.status_code not in {200,400}:
        raise AssertionError("Unexpected response status code during user registration")

def test_user_login_success_sets_cookie():
    with TestClient(app) as client:
        username = f"user-{uuid4()}"
        ensure_user(client, username, "testpassword")
        response = client.post(
            "/login", data={"username": username, "password": "testpassword"}
            
        )
        assert response.status_code == 200
        assert COOKIE_NAME in response.cookies
