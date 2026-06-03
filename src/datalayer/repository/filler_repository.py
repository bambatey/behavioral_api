from typing import List
from firebase_admin.firestore_async import AsyncClient

from ..model import Filler
from ._firestore_base_repository import FirestoreBaseRepository


class FillerRepository(FirestoreBaseRepository[Filler]):
    def __init__(self, db: AsyncClient):
        super().__init__(db, Filler, "fillers")

    async def list_active_ordered(self) -> List[Filler]:
        items = await self.find_by(is_active=True)
        items.sort(key=lambda f: f.order_index)
        return items

    async def list_all_ordered(self) -> List[Filler]:
        items = await self.get_all()
        items.sort(key=lambda f: f.order_index)
        return items
