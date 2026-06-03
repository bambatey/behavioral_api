import random
from typing import Dict, List, TYPE_CHECKING

from src.datalayer.model import (
    BIAS_OBJECT,
    BIAS_SUBJECT,
    Context,
    Filler,
    Participant,
    Sentence,
)
from src.datalayer.repository import (
    AssignmentCounterRepository,
    ContextRepository,
    FillerRepository,
    ParticipantRepository,
    SentenceRepository,
)

if TYPE_CHECKING:
    from firebase_admin.firestore_async import AsyncClient


CYCLE_USERS = 12  # 12 users complete one Latin-square cycle
CONTEXTS_PER_USER = 24
POSITIONS_PER_CONTEXT = 6


class AssignmentService:
    """Builds a user's trial set via the Latin-square algorithm + filler interleaving."""

    def __init__(self, db: "AsyncClient"):
        self.db = db
        self.context_repo = ContextRepository(db)
        self.sentence_repo = SentenceRepository(db)
        self.filler_repo = FillerRepository(db)
        self.counter_repo = AssignmentCounterRepository(db)
        self.participant_repo = ParticipantRepository(db)

    async def start_session(self, participant_name: str) -> Dict:
        """
        Allocate a Latin-square slot for the new participant, build their trial set,
        persist the Participant record, and return everything the frontend needs.
        """
        contexts = await self.context_repo.list_active_ordered()
        if len(contexts) < CONTEXTS_PER_USER:
            raise ValueError(
                f"Need at least {CONTEXTS_PER_USER} active contexts, got {len(contexts)}."
            )
        # Take exactly 24 contexts (in case admin added extra)
        contexts = contexts[:CONTEXTS_PER_USER]

        sentences_by_context = await self._load_sentences_indexed(contexts)
        fillers = await self.filler_repo.list_active_ordered()

        user_index = await self.counter_repo.next_index(modulo=CYCLE_USERS)

        critical_trials = self._build_critical_trials(user_index, contexts, sentences_by_context)
        filler_trials = self._build_filler_trials(fillers)

        all_trials = critical_trials + filler_trials
        random.shuffle(all_trials)
        for i, trial in enumerate(all_trials):
            trial["trial_index"] = i

        participant = Participant.create(name=participant_name, assignment_index=user_index)
        await self.participant_repo.save(participant)

        return {
            "participant_id": participant.id,
            "session_id": participant.session_id,
            "assignment_index": user_index,
            "trials": all_trials,
            "critical_count": len(critical_trials),
            "filler_count": len(filler_trials),
        }

    async def _load_sentences_indexed(
        self, contexts: List[Context]
    ) -> Dict[str, Dict]:
        """Returns {context_id: {(bias, position): Sentence}} for fast lookup."""
        index: Dict[str, Dict] = {}
        for c in contexts:
            sentences = await self.sentence_repo.find_active_by_context(c.id)
            ctx_index: Dict = {}
            for s in sentences:
                ctx_index[(s.bias, s.position)] = s
            index[c.id] = ctx_index
        return index

    def _build_critical_trials(
        self,
        user_index: int,
        contexts: List[Context],
        sentences_by_context: Dict[str, Dict],
    ) -> List[Dict]:
        trials = []
        for c, context in enumerate(contexts):
            position = ((c + user_index) % POSITIONS_PER_CONTEXT) + 1
            bias_idx = ((c // POSITIONS_PER_CONTEXT) + (user_index // POSITIONS_PER_CONTEXT)) % 2
            bias = BIAS_SUBJECT if bias_idx == 0 else BIAS_OBJECT
            ctx_index = sentences_by_context.get(context.id, {})
            sentence = ctx_index.get((bias, position))
            if sentence is None:
                raise ValueError(
                    f"Context '{context.title}' (order {context.order_index}) is missing "
                    f"bias={bias}, position={position}. Admin must fill all 12 sentences per context."
                )
            trials.append({
                "is_filler": False,
                "context_id": context.id,
                "context_text": context.text,
                "sentence_id": sentence.id,
                "sentence_text": sentence.text,
                "bias": sentence.bias,
                "position": sentence.position,
                "correct_answer": sentence.correct_answer,
            })
        return trials

    def _build_filler_trials(self, fillers: List[Filler]) -> List[Dict]:
        return [
            {
                "is_filler": True,
                "filler_id": f.id,
                "context_text": f.context_text,
                "sentence_text": f.sentence_text,
                "correct_answer": f.correct_answer,
            }
            for f in fillers
        ]
