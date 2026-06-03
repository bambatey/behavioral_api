from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

from .sentence import BIAS_OBJECT, BIAS_SUBJECT


@dataclass
class Context:
    """A context unit. 48 of these form the pool: 24 subject-biased + 24 object-biased."""
    id: str
    title: str
    text: str
    bias: str  # "subject" | "object"
    order_index: int
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(title: str, text: str, bias: str, order_index: int) -> "Context":
        if bias not in (BIAS_SUBJECT, BIAS_OBJECT):
            raise ValueError(f"bias must be 'subject' or 'object', got: {bias}")
        return Context(
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            bias=bias,
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
    def from_dict(data: dict) -> "Context":
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        # Tolerate documents that pre-date this field
        data.setdefault("bias", BIAS_SUBJECT)
        # Drop any unknown legacy keys to avoid TypeError
        known = {"id", "title", "text", "bias", "order_index", "is_active", "created_at", "updated_at"}
        data = {k: v for k, v in data.items() if k in known}
        return Context(**data)
