import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.customers.repository import InMemoryCustomerRepository, get_customer_repository

AUTH = {"Authorization": "Bearer ll_test_123"}


@pytest.fixture
def client():
    repo = InMemoryCustomerRepository()
    app.dependency_overrides[get_customer_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.pop(get_customer_repository, None)


def test_create_customer_returns_201_with_envelope(client):
    resp = client.post(
        "/v1/customers",
        headers={**AUTH, "Idempotency-Key": "key-1"},
        json={"email": "gym@example.com"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["object"] == "customer"
    assert body["id"].startswith("cus_")
    assert body["email"] == "gym@example.com"
    assert body["livemode"] is False
    assert resp.headers["Location"] == f"/v1/customers/{body['id']}"


def test_get_customer_returns_the_created_customer(client):
    created = client.post(
        "/v1/customers",
        headers={**AUTH, "Idempotency-Key": "key-get-1"},
        json={"email": "clinic@example.com"},
    ).json()

    resp = client.get(f"/v1/customers/{created['id']}", headers=AUTH)

    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["object"] == "customer"
    assert resp.json()["email"] == "clinic@example.com"


def test_get_unknown_customer_returns_404_problem_json(client):
    resp = client.get("/v1/customers/cus_doesnotexist", headers=AUTH)

    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == 404
    assert body["title"] == "Customer Not Found"
    assert "cus_doesnotexist" in body["detail"]
    assert body["code"] == "customer_not_found"


def test_live_key_sets_livemode_true(client):
    resp = client.post(
        "/v1/customers",
        headers={"Authorization": "Bearer ll_live_123", "Idempotency-Key": "key-live"},
        json={"email": "live@example.com"},
    )

    assert resp.status_code == 201
    assert resp.json()["livemode"] is True
