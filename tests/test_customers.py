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
