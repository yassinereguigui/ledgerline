from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer ll_test_123"}


def test_create_customer_returns_201_with_envelope():
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


def test_get_customer_returns_the_created_customer():
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


def test_get_unknown_customer_returns_404_problem_json():
    resp = client.get("/v1/customers/cus_doesnotexist", headers=AUTH)

    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["status"] == 404
    assert resp.json()["title"]


def test_missing_api_key_returns_401_problem_json():
    resp = client.post(
        "v1/customers",
        headers={"Idempotency-key": "key-noauth"},
        json={"email": "gym@example.com"},
    )

    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["www-authenticate"] == "Bearer"
    assert resp.json()["status"] == 401
