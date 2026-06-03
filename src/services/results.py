from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.datalayer.model import Participant, TrialResult
from src.datalayer.repository import ParticipantRepository, TrialResultRepository

if TYPE_CHECKING:
    from firebase_admin.firestore_async import AsyncClient


class ResultsService:
    """Persist trial responses against an already-created participant session."""

    def __init__(self, db: "AsyncClient"):
        self.db = db
        self.participant_repo = ParticipantRepository(db)
        self.trial_repo = TrialResultRepository(db)

    async def submit_session(
        self,
        participant_id: str,
        trials: List[Dict[str, Any]],
    ) -> int:
        participant = await self.participant_repo.get_by_id(participant_id)
        if participant is None:
            raise ValueError(f"Participant '{participant_id}' not found")

        trial_results = [
            TrialResult.create(participant.id, participant.name, trial)
            for trial in trials
            if trial.get("trial_index") is not None
        ]
        if trial_results:
            await self.trial_repo.save_all(trial_results)
        return len(trial_results)

    async def get_participant_results(self, participant_id: str) -> Optional[Dict[str, Any]]:
        participant = await self.participant_repo.get_by_id(participant_id)
        if not participant:
            return None
        trials = await self.trial_repo.find_by_participant_id(participant_id)
        trials.sort(key=lambda t: t.trial_index if t.trial_index is not None else 0)
        return {"participant": participant, "trials": trials}

    async def get_all_participants(self) -> List[Participant]:
        return await self.participant_repo.get_all()
