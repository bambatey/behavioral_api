from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid


@dataclass
class Participant:
    """A test participant. assignment_index (0..11) determines their Latin-square slot."""
    id: str
    name: str
    assignment_index: int
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(name: str, assignment_index: int) -> "Participant":
        return Participant(
            id=str(uuid.uuid4()),
            name=name,
            assignment_index=assignment_index,
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
        )

    def to_dict(self):
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: dict) -> "Participant":
        data = data.copy()
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        # Tolerate legacy keys (e.g., "test_type" from the old SPR/GJ schema)
        known = {"id", "name", "assignment_index", "session_id", "created_at"}
        data = {k: v for k, v in data.items() if k in known}
        # Default for docs that predate assignment_index
        data.setdefault("assignment_index", -1)
        return Participant(**data)
