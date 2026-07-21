from pathlib import Path
import logging

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app
from app.customers.repository import InMemoryCustomerRepository, get_customer_repository
from app.problems import ErrorCode, FieldErrorCode

SPEC_PATH = Path(__file__).resolve().parent.parent / "openapi.yaml"


class _BoomRepository:
    def add(self, customer: dict) -> None:
        raise RuntimeError("boom")

    def get(self, customer_id: str):
        raise RuntimeError("boom")


@pytest.fixture
def client():
    repo = InMemoryCustomerRepository()
    app.dependency_overrides[get_customer_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.pop(get_customer_repository, None)


@pytest.fixture
def raising_client():
    app.dependency_overrides[get_customer_repository] = lambda: _BoomRepository
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.pop(get_customer_repository, None)


@pytest.mark.skipif(
    not SPEC_PATH.exists(),
    reason="openapi.yaml isn't copied into the mutmut sandbox; drift check runs against the real tree only",
)
def test_error_codes_match_spec():
    spec = yaml.safe_load(SPEC_PATH.read_text())
    spec_codes = set(
        spec["components"]["schemas"]["ProblemDetail"]["properties"]["code"]["enum"]
    )
    assert {code.value for code in ErrorCode} == spec_codes


@pytest.mark.skipif(
    not SPEC_PATH.exists(),
    reason="openapi.yaml isn't copied into the mutmut sandbox; drift check runs against the real tree only",
)
def test_field_error_codes_match_spec():
    spec = yaml.safe_load(SPEC_PATH.read_text())
    errors_schema = spec["components"]["schemas"]["ValidationProblemDetail"]["allOf"][1]
    spec_codes = set(
        errors_schema["properties"]["errors"]["items"]["properties"]["code"]["enum"]
    )
    assert {code.value for code in FieldErrorCode} == spec_codes


def test_missing_api_key_returns_401_problem_json(client):
    resp = client.post(
        "/v1/customers",
        headers={"Idempotency-key": "key-noauth"},
        json={"email": "gym@example.com"},
    )

    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["www-authenticate"] == "Bearer"
    body = resp.json()
    assert body["status"] == 401
    assert body["type"] == "https://api.ledgerline.com/problems/unauthorized"
    assert body["title"] == "Unauthorized"
    assert body["detail"]
    assert body["code"] == "unauthorized"


def test_validation_error_returns_422_problem_json(client):
    resp = client.post(
        "/v1/customers",
        headers={"Authorization": "Bearer ll_test_123", "Idempotency-key": "k-422"},
        json={},
    )

    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == 422
    assert body["title"] == "Unprocessable Entity"
    assert body["code"] == "validation_error"
    assert body["type"] == "https://api.ledgerline.com/problems/validation-error"
    assert body["detail"]
    assert isinstance(body["errors"], list) and body["errors"]
    first = body["errors"][0]
    assert first["field"] == "email"
    assert first["code"] == "required"
    assert "message" in first


def test_extra_field_rejected_with_422(client):
    resp = client.post(
        "/v1/customers",
        headers={"Authorization": "Bearer ll_test_123", "Idempotency-Key": "k-422x"},
        json={"email": "gym@example.com", "emial": "typo"},
    )

    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")
    codes = [e["code"] for e in resp.json()["errors"]]
    assert "unknown_field" in codes
    assert all("message" in e for e in resp.json()["errors"])


def test_unknown_route_returns_404_problem_json(client):
    resp = client.get("/v1/nonexistant")

    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["code"] == "not_found"
    assert body["type"] == "about:blank"


def test_method_not_allowed_returns_405_problem_json(client):
    resp = client.delete("/v1/customers")

    assert resp.status_code == 405
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["allow"] == "POST"
    body = resp.json()
    assert body["status"] == 405
    assert body["code"] == "method_not_allowed"
    assert body["title"] == "Method Not Allowed"
    assert body["type"] == "about:blank"


def test_unhandled_error_returns_500_problem_json(raising_client, caplog):
    with caplog.at_level(logging.ERROR, logger="ledgerline"):
        resp = raising_client.get(
            "/v1/customers/cus_whatever",
            headers={"Authorization": "Bearer ll_test_123"},
        )

    assert resp.status_code == 500
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == 500
    assert body["code"] == "internal_error"
    assert body["title"] == "Internal Server Error"
    assert body["type"] == "about:blank"
    assert "detail" not in body
    assert "boom" not in resp.text
    assert any(record.exc_info for record in caplog.records)


def test_wrong_type_maps_to_invalid_type(client):
    resp = client.post(
        "/v1/customers",
        headers={"Authorization": "Bearer ll_test_123"},
        json={"email": 123},
    )

    assert resp.status_code == 422
    err = resp.json()["errors"][0]
    assert err["field"] == "email"
    assert err["code"] == "invalid_type"


def test_non_object_body_maps_to_root_and_invalid(client):
    resp = client.post(
        "/v1/customers",
        headers={
            "Authorization": "Bearer ll_test_123",
            "Content-Type": "application/json",
        },
        content="[1, 2, 3]",
    )
    assert resp.status_code == 422
    err = resp.json()["errors"][0]
    assert err["field"] == "(root)"
    assert err["code"] == "invalid"
