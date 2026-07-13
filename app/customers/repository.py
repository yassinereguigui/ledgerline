from typing import Protocol


class CustomerRepository(Protocol):
    def add(self, customer: dict) -> None: ...
    def get(self, customer_id: str) -> dict | None: ...


class InMemoryCustomerRepository:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def add(self, customer: dict) -> None:
        self._store[customer["id"]] = customer

    def get(self, customer_id: str) -> dict | None:
        return self._store.get(customer_id)
