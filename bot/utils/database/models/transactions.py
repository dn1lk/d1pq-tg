import decimal
from typing import Annotated, ClassVar

from utils.database import types
from utils.database.base import Column, Index

from .base import WithDates


class Transactions(WithDates):
    __tablename__: ClassVar[str] = "transactions"
    __indices__: ClassVar[list[Index]] = [
        Index("user_chat_ids", ["user_id", "chat_id"], ["amount"]),
    ]

    __slots__ = (
        "amount",
        "chat_id",
        "created_at",
        "id",
        "token",
        "updated_at",
        "user_id",
    )

    id: Annotated[int, Column(types.Uint64, is_primary_key=True)]
    user_id: Annotated[int, Column(types.Int64)]
    chat_id: Annotated[int, Column(types.Int64)]
    amount: Annotated[decimal.Decimal, Column(types.Decimal)]

    async def delete(self) -> None:
        pass
