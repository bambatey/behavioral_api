from typing import Optional, List

from ..model import TrialResult
from ._firestore_base_repository import FirestoreBaseRepository


class TrialResultRepository(FirestoreBaseRepository[TrialResult]):
    """Repository for TrialResult entities"""

    def __init__(self, db: AsyncClient):
        super().__init__(db, TrialResult, "trial_results")

    async def find_by_participant_id(self, participant_id: str) -> List[TrialResult]:
        """Get all trial results for a specific participant"""
        return await self.find_by(participant_id=participant_id)

    async def find_by_participant_and_test_type(
        self, participant_id: str, test_type: str
    ) -> List[TrialResult]:
        """Get trial results for a participant filtered by test type"""
        results = await self.find_by(participant_id=participant_id)
        return [r for r in results if r.test_type == test_type]

    async def find_by_test_type(self, test_type: str) -> List[TrialResult]:
        """Get all trial results for a specific test type"""
        return await self.find_by(test_type=test_type)

    async def count_by_participant(self, participant_id: str) -> int:
        """Count trials for a specific participant"""
        return await self.count(participant_id=participant_id)
