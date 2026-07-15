from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    name: str | None = None
    description: str | None = None
    phone: str | None = None
