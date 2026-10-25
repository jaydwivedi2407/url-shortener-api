
import pytest
import main

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Har test ke liye alag temporary database
    test_database = tmp_path / "test_urls.db"

    monkeypatch.setattr(main, "DATABASE", str(test_database))

    # App startup par database initialize hoga
    with TestClient(main.app) as test_client:
        yield test_client


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "URL Shortener API is running"


def test_create_link(client):
    response = client.post(
        "/links",
        json={
            "url": "https://example.com",
            "alias": "testcreate01"
        }
    )

    assert response.status_code == 201
    assert response.json()["code"] == "testcreate01"
    assert response.json()["original_url"] == "https://example.com/"


def test_duplicate_alias(client):
    client.post(
        "/links",
        json={
            "url": "https://example.com",
            "alias": "testduplicate01"
        }
    )

    response = client.post(
        "/links",
        json={
            "url": "https://google.com",
            "alias": "testduplicate01"
        }
    )

    assert response.status_code == 409


def test_unknown_code(client):
    response = client.get("/thiscodecannotexist999")

    assert response.status_code == 404


def test_past_expiry_rejected(client):
    response = client.post(
        "/links",
        json={
            "url": "https://example.com",
            "alias": "testexpiry01",
            "expires_at": "2020-01-01T00:00:00Z"
        }
    )

    assert response.status_code == 422


def test_invalid_url(client):
    response = client.post(
        "/links",
        json={
            "url": "not-a-valid-url",
            "alias": "testinvalid01"
        }
    )

    assert response.status_code == 422


def test_expired_link_returns_410(client):
    alias = "testexpired410"

    expiry = datetime.now(timezone.utc) + timedelta(seconds=2)

    create_response = client.post(
        "/links",
        json={
            "url": "https://example.com",
            "alias": alias,
            "expires_at": expiry.isoformat()
        }
    )

    assert create_response.status_code == 201

    import time
    time.sleep(3)

    response = client.get(
        f"/{alias}",
        follow_redirects=False
    )

    assert response.status_code == 410
