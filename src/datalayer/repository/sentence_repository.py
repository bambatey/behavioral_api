from typing import List, Optional
from firebase_admin.firestore_async import AsyncClient

from ..model import Sentence
from ._firestore_base_repository import FirestoreBaseRepository


class SentenceRepository(FirestoreBaseRepository[Sentence]):
    def __init__(self, db: AsyncClient):
        super().__init__(db, Sentence, "sentences")

    async def find_by_context(self, context_id: str) -> List[Sentence]:
        items = await self.find_by(context_id=context_id)
        items.sort(key=lambda s: s.position)
        return items

    async def find_active_by_context(self, context_id: str) -> List[Sentence]:
        items = await self.find_by(context_id=context_id)
        return [s for s in items if s.is_active]

    async def find_one_by_context_position(
        self, context_id: str, position: int
    ) -> Optional[Sentence]:
        items = await self.find_by(context_id=context_id, position=position)
        return items[0] if items else None

    async def delete_by_context(self, context_id: str) -> int:
        items = await self.find_by(context_id=context_id)
        for s in items:
            await self.delete_by_id(s.id)
        return len(items)
