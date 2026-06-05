from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.datalayer.model import Participant, TrialResult
from src.datalayer.repository import (
    ContextRepository,
    FillerRepository,
    ParticipantRepository,
    SentenceRepository,
    TrialResultRepository,
)

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

        # Client now only sends {trial_index, sentence_id|filler_id, response, rt}.
        # Rehydrate context/sentence/filler metadata server-side so DevTools-leaked
        # `correct_answer` etc. can't influence the saved record.
        sentence_repo = SentenceRepository(self.db)
        filler_repo = FillerRepository(self.db)
        context_repo = ContextRepository(self.db)

        sentence_index = {s.id: s for s in await sentence_repo.get_all()}
        filler_index = {f.id: f for f in await filler_repo.get_all()}
        context_index = {c.id: c for c in await context_repo.get_all()}

        enriched: List[Dict[str, Any]] = []
        for t in trials:
            if t.get("trial_index") is None:
                continue
            sentence_id = t.get("sentence_id")
            filler_id = t.get("filler_id")
            payload = {
                "trial_index": t["trial_index"],
                "response": t.get("response"),
                "rt": t.get("rt"),
            }
            if sentence_id and sentence_id in sentence_index:
                s = sentence_index[sentence_id]
                ctx = context_index.get(s.context_id)
                payload.update({
                    "is_filler": False,
                    "sentence_id": s.id,
                    "context_id": s.context_id,
                    "context_text": ctx.text if ctx else None,
                    "sentence_text": s.text,
                    "bias": ctx.bias if ctx else None,
                    "position": s.position,
                    "correct_answer": s.correct_answer,
                })
            elif filler_id and filler_id in filler_index:
                f = filler_index[filler_id]
                payload.update({
                    "is_filler": True,
                    "filler_id": f.id,
                    "context_text": f.context_text,
                    "sentence_text": f.sentence_text,
                    "correct_answer": f.correct_answer,
                })
            else:
                # No recognised id — skip rather than persist a useless record
                continue
            enriched.append(payload)

        trial_results = [
            TrialResult.create(participant.id, participant.name, t) for t in enriched
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

    async def delete_participant(self, participant_id: str) -> int:
        """Delete a participant and every trial_result they own.
        Returns the count of trial_results removed."""
        trials = await self.trial_repo.find_by_participant_id(participant_id)
        for t in trials:
            await self.trial_repo.delete_by_id(t.id)
        await self.participant_repo.delete_by_id(participant_id)
        return len(trials)
