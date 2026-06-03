from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class TrialResult:
    """A single trial response. Covers both critical (context+sentence) and filler items."""
    id: str
    participant_id: str
    participant_name: str
    trial_index: int
    is_filler: bool

    # Stimulus identifiers (for critical: sentence_id+context_id; for filler: filler_id)
    sentence_id: Optional[str] = None
    context_id: Optional[str] = None
    filler_id: Optional[str] = None

    # Stimulus content (denormalized for analysis convenience)
    context_text: Optional[str] = None
    sentence_text: Optional[str] = None

    # Critical-only fields
    bias: Optional[str] = None  # "subject" | "object"
    position: Optional[int] = None  # 1..6

    # Response — 1..7 Likert scale (1 = hiç doğru değil, 7 = çok doğru)
    response: Optional[int] = None
    correct_answer: Optional[bool] = None  # admin'in bilgisi, ham veri olarak kalır (analiz dışı)
    rt: Optional[float] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        participant_id: str,
        participant_name: str,
        trial_data: dict,
    ) -> "TrialResult":
        raw_response = trial_data.get("response")
        response: Optional[int] = None
        if raw_response is not None:
            try:
                response = int(raw_response)
            except (TypeError, ValueError):
                response = None

        return TrialResult(
            id=str(uuid.uuid4()),
            participant_id=participant_id,
            participant_name=participant_name,
            trial_index=trial_data.get("trial_index"),
            is_filler=bool(trial_data.get("is_filler", False)),
            sentence_id=trial_data.get("sentence_id"),
            context_id=trial_data.get("context_id"),
            filler_id=trial_data.get("filler_id"),
            context_text=trial_data.get("context_text"),
            sentence_text=trial_data.get("sentence_text"),
            bias=trial_data.get("bias"),
            position=trial_data.get("position"),
            response=response,
            correct_answer=trial_data.get("correct_answer"),
            rt=trial_data.get("rt"),
            created_at=datetime.utcnow(),
        )

    def to_dict(self):
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def from_dict(data: dict) -> "TrialResult":
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        # Provide defaults for fields possibly absent in older docs
        data.setdefault("is_filler", False)
        # Drop legacy keys (e.g., "accuracy" field that used to be computed server-side)
        known = {
            "id", "participant_id", "participant_name", "trial_index", "is_filler",
            "sentence_id", "context_id", "filler_id", "context_text", "sentence_text",
            "bias", "position", "response", "correct_answer", "rt", "created_at",
        }
        data = {k: v for k, v in data.items() if k in known}
        return TrialResult(**data)
