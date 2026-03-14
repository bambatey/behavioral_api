from typing import List, Dict, Any

from datalayer.model import Participant, TrialResult
from datalayer.repository import ParticipantRepository, TrialResultRepository


class ResultsService:
    """Service for handling test results submission and storage"""

    def __init__(self, db: AsyncClient):
        self.db = db
        self.participant_repo = ParticipantRepository(db)
        self.trial_repo = TrialResultRepository(db)

    async def save_session(
        self, participant_name: str, test_type: str, trials: List[Dict[str, Any]]
    ) -> str:
        """
        Save a complete test session with all trial results.

        Args:
            participant_name: Name of the participant
            test_type: Type of test ("spr" or "gj")
            trials: List of trial data from jsPsych

        Returns:
            participant_id: The ID of the saved participant
        """
        try:
            # Create and save participant record
            participant = Participant.create(participant_name, test_type)
            await self.participant_repo.save(participant)

            # Convert trial data to TrialResult objects and save in batch
            trial_results = [
                TrialResult.create(participant.id, participant_name, test_type, trial)
                for trial in trials
                # Filter out non-response trials (like fixation crosses)
                if trial.get("trial_index") is not None
            ]

            if trial_results:
                await self.trial_repo.save_all(trial_results)

            return participant.id
        except Exception as e:
            print(f"Error saving session: {e}")
            raise

    async def get_participant_results(self, participant_id: str) -> Dict[str, Any]:
        """
        Get all results for a participant.

        Returns:
            dict with participant info and trial results
        """
        try:
            participant = await self.participant_repo.get_by_id(participant_id)
            if not participant:
                return None

            trials = await self.trial_repo.find_by_participant_id(participant_id)

            return {
                "participant": participant,
                "trials": trials,
                "trial_count": len(trials),
            }
        except Exception as e:
            print(f"Error getting participant results: {e}")
            raise

    async def get_all_participants(self) -> List[Participant]:
        """Get all participants"""
        try:
            return await self.participant_repo.get_all()
        except Exception as e:
            print(f"Error getting all participants: {e}")
            raise

    async def get_test_results_by_type(self, test_type: str) -> List[TrialResult]:
        """Get all results for a specific test type"""
        try:
            return await self.trial_repo.find_by_test_type(test_type)
        except Exception as e:
            print(f"Error getting results by test type: {e}")
            raise
