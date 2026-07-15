import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status

from app.customers.repository import InMemoryCustomerRepository
from app.customers.schemas import CustomerCreate
from app.dependencies import require_api_key

router = APIRouter(prefix="/v1", tags=["customers"])
_repo = InMemoryCustomerRepository()


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate, response: Response, livemode: bool = Depends(require_api_key)
) -> dict:

    customer: dict = {
        "id": f"cus_{secrets.token_hex(12)}",
        "object": "customer",
        "created": datetime.now(timezone.utc).isoformat(),
        "livemode": livemode,
        "email": body.email,
    }

    for field in ("name", "description", "phone"):
        value = getattr(body, field)
        if value is not None:
            customer[field] = value

    _repo.add(customer)
    response.headers["Location"] = f"/v1/customers/{customer['id']}"
    return customer
