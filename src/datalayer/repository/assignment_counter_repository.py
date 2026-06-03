from firebase_admin.firestore_async import AsyncClient
from google.cloud.firestore_v1 import Increment

from ..model import AssignmentCounter, COUNTER_DOC_ID

COLLECTION = "assignment_counter"


class AssignmentCounterRepository:
    """Atomic counter used to assign each new session a Latin-square slot."""

    def __init__(self, db: AsyncClient):
        self.db = db

    async def next_index(self, modulo: int = 12) -> int:
        """Atomically increment the global counter and return (new_value - 1) mod `modulo`."""
        doc_ref = self.db.collection(COLLECTION).document(COUNTER_DOC_ID)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            await doc_ref.set({"counter": 1})
            return 0 % modulo
        await doc_ref.update({"counter": Increment(1)})
        snapshot = await doc_ref.get()
        new_value = int(snapshot.to_dict().get("counter", 1))
        return (new_value - 1) % modulo

    async def peek(self) -> int:
        doc_ref = self.db.collection(COLLECTION).document(COUNTER_DOC_ID)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return 0
        return int(snapshot.to_dict().get("counter", 0))

    async def reset(self) -> None:
        await self.db.collection(COLLECTION).document(COUNTER_DOC_ID).set({"counter": 0})
