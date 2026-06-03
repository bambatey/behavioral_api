from dataclasses import dataclass, asdict


COUNTER_DOC_ID = "global"


@dataclass
class AssignmentCounter:
    """Single-document counter for Latin-square user assignment. (counter mod 12) = user index."""
    id: str
    counter: int

    @staticmethod
    def initial() -> "AssignmentCounter":
        return AssignmentCounter(id=COUNTER_DOC_ID, counter=0)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "AssignmentCounter":
        return AssignmentCounter(id=data.get("id", COUNTER_DOC_ID), counter=int(data.get("counter", 0)))
