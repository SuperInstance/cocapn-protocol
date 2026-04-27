from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from cocapn_protocol.bottle import Bottle


@dataclass
class Channel:
    """Simple channel abstraction that holds a send callback."""

    send: Callable[[Bottle], None]


RouteTable = Dict[str, Channel]


class DeadbandRouter:
    """Routes messages according to priority rules.

    - P0: send immediately (blocking)
    - P1: queue for next tick
    - P2: batch until flush_p2_batch() is called
    """

    def __init__(self) -> None:
        self._p1_queue: List[tuple[Bottle, RouteTable]] = []
        self._p2_batches: Dict[str, List[Bottle]] = defaultdict(list)

    def route(self, msg: Bottle, route_table: RouteTable) -> None:
        """Decide delivery strategy based on msg.priority."""
        priority = (msg.priority or "P2").upper()

        if priority == "P0":
            self._send_now(msg, route_table)
        elif priority == "P1":
            self._p1_queue.append((msg, route_table))
        else:
            # P2 (or anything else) -> batch
            for agent_name in route_table:
                self._p2_batches[agent_name].append(msg)

    def flush_p2_batch(self, route_table: RouteTable) -> None:
        """Send all accumulated P2 messages."""
        for agent_name, channel in route_table.items():
            batch = self._p2_batches.get(agent_name, [])
            if not batch:
                continue
            for msg in batch:
                try:
                    channel.send(msg)
                except Exception:
                    # Drop on error; real impl may retry or dead-letter
                    pass
            self._p2_batches[agent_name] = []

    def tick(self, route_table: RouteTable) -> None:
        """Process the P1 queue (call once per tick)."""
        queue = self._p1_queue
        self._p1_queue = []
        for msg, rt in queue:
            self._send_now(msg, rt)

    def _send_now(self, msg: Bottle, route_table: RouteTable) -> None:
        for agent_name, channel in route_table.items():
            try:
                channel.send(msg)
            except Exception:
                # Drop on error
                pass
