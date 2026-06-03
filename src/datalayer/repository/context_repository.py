from typing import List
from firebase_admin.firestore_async import AsyncClient
from datetime import datetime

from ..model import Context
from ._firestore_base_repository import FirestoreBaseRepository


class ContextRepository(FirestoreBaseRepository[Context]):
    def __init__(self, db: AsyncClient):
        super().__init__(db, Context, "contexts")

    async def list_active_ordered(self) -> List[Context]:
        items = await self.find_by(is_active=True)
        items.sort(key=lambda c: c.order_index)
        return items

    async def list_all_ordered(self) -> List[Context]:
        items = await self.get_all()
        items.sort(key=lambda c: c.order_index)
        return items
