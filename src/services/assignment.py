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


CYCLE_USERS = 12          # 12 users complete one Latin-square cycle
PAIRS_PER_USER = 24       # each user gets 24 critical trials
CONTEXTS_PER_BIAS = 24    # admin must provide 24 subject + 24 object contexts
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
        contexts = await self.context_repo.list_active_ordered()
        subject_contexts = sorted(
            (c for c in contexts if c.bias == BIAS_SUBJECT),
            key=lambda c: c.order_index,
        )
        object_contexts = sorted(
            (c for c in contexts if c.bias == BIAS_OBJECT),
            key=lambda c: c.order_index,
        )
        if len(subject_contexts) < CONTEXTS_PER_BIAS or len(object_contexts) < CONTEXTS_PER_BIAS:
            raise ValueError(
                f"Need {CONTEXTS_PER_BIAS} subject-biased and {CONTEXTS_PER_BIAS} object-biased "
                f"active contexts; got {len(subject_contexts)} subject and {len(object_contexts)} object."
            )
        subject_contexts = subject_contexts[:CONTEXTS_PER_BIAS]
        object_contexts = object_contexts[:CONTEXTS_PER_BIAS]

        sentence_index = await self._load_sentences_indexed(subject_contexts + object_contexts)
        fillers = await self.filler_repo.list_active_ordered()

        user_index = await self.counter_repo.next_index(modulo=CYCLE_USERS)

        critical_trials = self._build_critical_trials(
            user_index, subject_contexts, object_contexts, sentence_index
        )
        filler_trials = self._build_filler_trials(fillers)

        all_trials = critical_trials + filler_trials
        random.shuffle(all_trials)

        participant = Participant.create(name=participant_name, assignment_index=user_index)
        # Stash the shuffled render list on the participant doc so we can serve
        # trials one-by-one via /sessions/trial and never expose the full list.
        participant.trial_order = all_trials
        await self.participant_repo.save(participant)

        return {
            "participant_id": participant.id,
            "session_id": participant.session_id,
            "assignment_index": user_index,
            "total_count": len(all_trials),
            "critical_count": len(critical_trials),
            "filler_count": len(filler_trials),
        }

    async def get_trial(self, participant_id: str, trial_index: int) -> Dict:
        """Return a single trial's render payload by index, or None if out of range."""
        participant = await self.participant_repo.get_by_id(participant_id)
        if participant is None:
            return None
        order = participant.trial_order or []
        if not (0 <= trial_index < len(order)):
            return None
        return order[trial_index]

    async def _load_sentences_indexed(
        self, contexts: List[Context]
    ) -> Dict[str, Dict[int, Sentence]]:
        """Returns {context_id: {position: Sentence}} via a single get_all,
        then groups in-memory. Cuts Firestore reads from 48 to 1."""
        context_ids = {c.id for c in contexts}
        all_sentences = await self.sentence_repo.get_all()
        index: Dict[str, Dict[int, Sentence]] = {cid: {} for cid in context_ids}
        for s in all_sentences:
            if not s.is_active or s.context_id not in context_ids:
                continue
            index[s.context_id][s.position] = s
        return index

    def _build_critical_trials(
        self,
        user_index: int,
        subject_contexts: List[Context],
        object_contexts: List[Context],
        sentence_index: Dict[str, Dict[int, Sentence]],
    ) -> List[Dict]:
        """Only ship render data + sentence_id to the client.
        bias / position / correct_answer stay on the server so they can't be
        read out of DevTools and influence participants."""
        trials = []
        for i in range(PAIRS_PER_USER):
            position = ((i + user_index) % POSITIONS_PER_CONTEXT) + 1
            bias_idx = ((i // POSITIONS_PER_CONTEXT) + (user_index // POSITIONS_PER_CONTEXT)) % 2
            context = object_contexts[i] if bias_idx == 0 else subject_contexts[i]
            sentence = sentence_index.get(context.id, {}).get(position)
            if sentence is None:
                raise ValueError(
                    f"Context '{context.title}' (bias={context.bias}, order={context.order_index}) "
                    f"is missing position={position}. Each context needs all 6 sentences."
                )
            trials.append({
                "context_text": context.text,
                "sentence_text": sentence.text,
                "sentence_id": sentence.id,
            })
        return trials

    def _build_filler_trials(self, fillers: List[Filler]) -> List[Dict]:
        return [
            {
                "context_text": f.context_text,
                "sentence_text": f.sentence_text,
                "filler_id": f.id,
            }
            for f in fillers
        ]
