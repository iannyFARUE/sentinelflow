from __future__ import annotations

from pydantic import BaseModel, Field, conint, condecimal


Money = condecimal(max_digits=12, decimal_places=2)


class CheckBalanceIn(BaseModel):
    user_id: str = Field(..., min_length=1)


class CheckBalanceOut(BaseModel):
    user_id: str
    balance: Money
    currency: str


class ExecutePurchaseIn(BaseModel):
    user_id: str
    product_id: str
    qty: conint(ge=1, le=999) = 1
    idempotency_key: str = Field(..., min_length=8, max_length=80)
    confirm: bool = False  # must be True for actual execution


class ExecutePurchaseOut(BaseModel):
    transaction_id: str
    status: str
    total_amount: Money
    currency: str
    remaining_balance: Money


class UpdateDatabaseIn(BaseModel):
    # generic tool for demo; in practice you'd have specific ops
    table: str
    key: str
    value: str


class UpdateDatabaseOut(BaseModel):
    status: str


class SearchProductsIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=10)

class SearchProductsOut(BaseModel):
    results: list[dict]
