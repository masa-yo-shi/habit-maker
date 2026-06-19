from pathlib import Path
import sys

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app


def test_page1_renders_my_habits_timer_and_memo():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "htmx.org" in response.text
    assert 'id="my-habits-section"' in response.text
    assert 'id="timer-section"' in response.text
    assert 'id="page1-memo-section"' in response.text


def test_page2_renders_category_picker_and_calendar():
    with TestClient(app) as client:
        response = client.get("/page2")

    assert response.status_code == 200
    assert 'id="page2-category-picker"' in response.text
    assert 'id="my-habits-section"' in response.text
    assert 'id="calendar-section"' in response.text
    assert "Backend diary API" in response.text
    assert "Added diary entry CRUD endpoints and monthly calendar summaries." in response.text


def test_page1_memo_section_route_renders():
    with TestClient(app) as client:
        response = client.get("/ui/page1/memo")

    assert response.status_code == 200
    assert 'id="page1-memo-section"' in response.text


def test_create_memo_via_memos_endpoint():
    with TestClient(app) as client:
        # Initial check to see if a specific test memo exists (it shouldn't)
        response = client.get("/")
        assert "Test Memo Content" not in response.text

        # Create memo
        response = client.post("/memos", data={"memo_content": "Test Memo Content"})
        assert response.status_code == 200
        assert 'id="page1-memo-section"' in response.text
        assert "Test Memo Content" in response.text
        assert "今日のメモ" in response.text
