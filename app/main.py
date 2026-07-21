from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.customers.router import router as customers_router
from app.problems import (
    ProblemException,
    problem_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)

app = FastAPI(title="Ledgerline", version="0.1.0")
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ProblemException, problem_exception_handler)
app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
