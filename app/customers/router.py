import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status, Request

from app.customers.repository import CustomerRepository, get_customer_repository
from app.customers.schemas import CustomerCreate
from app.dependencies import require_api_key
from app.problems import ErrorCode, ProblemException, problem_type

router = APIRouter(prefix="/v1", tags=["customers"])


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    request: Request,
    response: Response,
    livemode: bool = Depends(require_api_key),
    repo: CustomerRepository = Depends(get_customer_repository),
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

    repo.add(customer)

    response.headers["Location"] = request.app.url_path_for(
        "get_customer", customer_id=customer["id"]
    )

    return customer


@router.get(
    "/customers/{customer_id}",
    name="get_customer",
    dependencies=[Depends(require_api_key)],
)
def get_customer(
    customer_id: str, repo: CustomerRepository = Depends(get_customer_repository)
) -> dict:

    customer = repo.get(customer_id)

    if customer is None:
        raise ProblemException(
            status=404,
            title="Customer Not Found",
            code=ErrorCode.CUSTOMER_NOT_FOUND,
            detail=f"No customer with id {customer_id} exists in this account",
            type_=problem_type("customer-not-found"),
        )

    return customer
