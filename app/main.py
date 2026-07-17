from fastapi import FastAPI
from app.customers.router import router as customers_router
from app.problems import ProblemException, problem_exception_handler

app = FastAPI(title="Ledgerline", version="0.1.0")
app.add_exception_handler(ProblemException, problem_exception_handler)
app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
