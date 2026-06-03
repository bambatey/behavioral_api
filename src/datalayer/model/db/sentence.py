from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


BIAS_SUBJECT = "subject"
BIAS_OBJECT = "object"


@dataclass
class Sentence:
    """A sentence belonging to a context. Per context: 6 subject-biased + 6 object-biased = 12."""
    id: str
    context_id: str
    bias: str  # "subject" | "object"
    position: int  # 1..6
    text: str
    correct_answer: bool  # True if sentence is judged "correct/grammatical"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        context_id: str,
        bias: str,
        position: int,
        text: str,
        correct_answer: bool,
    ) -> "Sentence":
        if bias not in (BIAS_SUBJECT, BIAS_OBJECT):
            raise ValueError(f"bias must be 'subject' or 'object', got: {bias}")
        if not 1 <= position <= 6:
            raise ValueError(f"position must be in 1..6, got: {position}")
        return Sentence(
            id=str(uuid.uuid4()),
            context_id=context_id,
            bias=bias,
            position=position,
            text=text,
            correct_answer=correct_answer,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def to_dict(self):
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: dict) -> "Sentence":
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return Sentence(**data)
