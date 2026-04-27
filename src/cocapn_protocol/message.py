from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Priority(Enum):
    """Message priority levels for the Cocapn fleet."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class FleetMessage:
    """A standard message exchanged between fleet agents."""

    sender: str
    recipient: str
    priority: Priority
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if isinstance(self.priority, str):
            try:
                self.priority = Priority(self.priority)
            except ValueError as exc:
                raise ValueError(f"Invalid priority: {self.priority}") from exc
        elif not isinstance(self.priority, Priority):
            raise ValueError(f"Invalid priority: {self.priority}")

    def serialize(self) -> bytes:
        """Serialize the message to JSON bytes."""
        data = asdict(self)
        data["priority"] = self.priority.value
        return json.dumps(data, separators=(",", ":")).encode("utf-8")

    @classmethod
    def deserialize(cls, data: bytes) -> FleetMessage:
        """Deserialize JSON bytes into a FleetMessage."""
        decoded = json.loads(data.decode("utf-8"))
        return cls(**decoded)
