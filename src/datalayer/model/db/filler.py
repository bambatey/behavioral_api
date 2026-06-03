from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Filler:
    """Filler trial — same context+sentence shape as critical trials, but not analyzed."""
    id: str
    context_text: str
    sentence_text: str
    correct_answer: bool
    order_index: int
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        context_text: str,
        sentence_text: str,
        correct_answer: bool,
        order_index: int,
    ) -> "Filler":
        return Filler(
            id=str(uuid.uuid4()),
            context_text=context_text,
            sentence_text=sentence_text,
            correct_answer=correct_answer,
            order_index=order_index,
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
    def from_dict(data: dict) -> "Filler":
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return Filler(**data)
