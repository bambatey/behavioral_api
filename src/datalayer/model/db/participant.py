from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Participant:
    """Model representing a test participant session"""
    id: str  # Firestore doc ID (UUID)
    name: str
    test_type: str  # "spr" or "gj"
    session_id: str
    created_at: datetime

    @staticmethod
    def create(name: str, test_type: str) -> "Participant":
        """Factory method to create a new participant"""
        return Participant(
            id=str(uuid.uuid4()),
            name=name,
            test_type=test_type,
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
        )

    def to_dict(self):
        """Convert to dictionary for Firestore serialization"""
        data = asdict(self)
        # Firestore doesn't serialize datetime objects directly in some cases
        data["created_at"] = self.created_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: dict) -> "Participant":
        """Reconstruct from Firestore document"""
        data = data.copy()
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return Participant(**data)
