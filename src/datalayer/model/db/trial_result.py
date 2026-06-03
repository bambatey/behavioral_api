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

    # Response
    response: Optional[str] = None  # "true" | "false"
    correct_answer: Optional[bool] = None
    accuracy: Optional[int] = None  # 1 if response matches correct_answer, else 0
    rt: Optional[float] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        participant_id: str,
        participant_name: str,
        trial_data: dict,
    ) -> "TrialResult":
        response = trial_data.get("response")
        correct_answer = trial_data.get("correct_answer")
        accuracy = None
        if response is not None and correct_answer is not None:
            response_bool = str(response).lower() in ("true", "1", "yes", "doğru", "dogru")
            accuracy = 1 if response_bool == bool(correct_answer) else 0

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
            response=str(response) if response is not None else None,
            correct_answer=correct_answer,
            accuracy=accuracy,
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
        return TrialResult(**data)
