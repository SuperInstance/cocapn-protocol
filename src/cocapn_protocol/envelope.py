from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .message import FleetMessage


@dataclass
class FleetEnvelope:
    """Wraps a FleetMessage with routing metadata."""

    message: FleetMessage
    hop_count: int = 0
    max_hops: int = 10
    return_path: list[str] = field(default_factory=list)
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        payload = json.dumps(
            {
                "sender": self.message.sender,
                "recipient": self.message.recipient,
                "priority": self.message.priority.value,
                "payload": self.message.payload,
                "timestamp": self.message.timestamp,
                "message_id": self.message.message_id,
                "trace_id": self.message.trace_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def verify_checksum(self) -> bool:
        """Validate the integrity of the wrapped message."""
        return self.checksum == self._compute_checksum()

    def add_hop(self, agent_name: str) -> None:
        """Record an intermediary agent and increment hop count."""
        self.return_path.append(agent_name)
        self.hop_count += 1
