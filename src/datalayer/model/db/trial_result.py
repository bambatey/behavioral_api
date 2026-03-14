from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class TrialResult:
    """Model representing a single trial result (for both SPR and GJ tests)"""
    id: str  # Firestore doc ID
    participant_id: str
    participant_name: str
    test_type: str  # "spr" or "gj"
    trial_index: int
    rt: Optional[float] = None
    response: Optional[str] = None
    task_type: Optional[str] = None  # "word_reading", "comprehension_check", "judgment", "fixation"

    # SPR-specific fields
    sentence_id: Optional[str] = None
    word: Optional[str] = None
    word_position: Optional[int] = None
    condition: Optional[str] = None

    # GJ-specific fields
    sentence: Optional[str] = None
    is_grammatical: Optional[bool] = None
    attrition_marker: Optional[str] = None
    accuracy: Optional[int] = None
    correct_answer: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        participant_id: str,
        participant_name: str,
        test_type: str,
        trial_data: dict
    ) -> "TrialResult":
        """Factory method to create a trial result from jsPsych trial data"""
        sentence_id = trial_data.get("sentence_id")
        if sentence_id is not None:
            sentence_id = str(sentence_id)

        return TrialResult(
            id=str(uuid.uuid4()),
            participant_id=participant_id,
            participant_name=participant_name,
            test_type=test_type,
            trial_index=trial_data.get("trial_index"),
            rt=trial_data.get("rt"),
            response=trial_data.get("response"),
            task_type=trial_data.get("task_type"),
            sentence_id=sentence_id,
            word=trial_data.get("word"),
            word_position=trial_data.get("word_position"),
            condition=trial_data.get("condition"),
            sentence=trial_data.get("sentence"),
            is_grammatical=trial_data.get("is_grammatical"),
            attrition_marker=trial_data.get("attrition_marker"),
            accuracy=trial_data.get("accuracy"),
            correct_answer=trial_data.get("correct_answer"),
            created_at=datetime.utcnow(),
        )

    def to_dict(self):
        """Convert to dictionary for Firestore serialization"""
        data = asdict(self)
        # Convert created_at to ISO format for Firestore
        data["created_at"] = self.created_at.isoformat()
        # Remove None values to keep Firestore documents clean
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def from_dict(data: dict) -> "TrialResult":
        """Reconstruct from Firestore document"""
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return TrialResult(**data)
