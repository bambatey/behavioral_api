from typing import Optional, List

from ..model import Participant
from ._firestore_base_repository import FirestoreBaseRepository


class ParticipantRepository(FirestoreBaseRepository[Participant]):
    """Repository for Participant entities"""

    def __init__(self, db: AsyncClient):
        super().__init__(db, Participant, "participants")

    async def find_by_name(self, name: str) -> List[Participant]:
        """Find participants by name"""
        return await self.find_by(name=name)

    async def find_by_session_id(self, session_id: str) -> Optional[Participant]:
        """Find participant by session_id"""
        return await self.find_one_by(session_id=session_id)

    async def find_by_test_type(self, test_type: str) -> List[Participant]:
        """Find all participants who took a specific test type"""
        return await self.find_by(test_type=test_type)
