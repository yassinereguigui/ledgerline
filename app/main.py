from fastapi import FastAPI
from app.customers.router import router as customers_router

app = FastAPI(title="Ledgerline", version="0.1.0")
app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
