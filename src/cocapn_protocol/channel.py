from __future__ import annotations

import socket
import threading
from abc import ABC, abstractmethod
from collections import deque
from typing import Callable


class Channel(ABC):
    """Abstract base class for transport channels."""

    @abstractmethod
    def send(self, msg: bytes) -> None:
        """Send a message over the channel."""
        ...

    @abstractmethod
    def receive(self) -> bytes:
        """Receive a message from the channel."""
        ...

    @abstractmethod
    def subscribe(self, handler: Callable[[bytes], None]) -> None:
        """Subscribe a handler to incoming messages."""
        ...


class InMemoryChannel(Channel):
    """In-memory channel backed by a deque."""

    def __init__(self):
        self._queue: deque[bytes] = deque()
        self._handlers: list[Callable[[bytes], None]] = []
        self._lock = threading.Lock()

    def send(self, msg: bytes) -> None:
        with self._lock:
            self._queue.append(msg)
        for handler in self._handlers:
            handler(msg)

    def receive(self) -> bytes:
        with self._lock:
            if not self._queue:
                raise IndexError("No messages in channel")
            return self._queue.popleft()

    def subscribe(self, handler: Callable[[bytes], None]) -> None:
        self._handlers.append(handler)


class UDPChannel(Channel):
    """UDP channel supporting broadcast discovery."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        broadcast: bool = False,
    ):
        self.host = host
        self.port = port
        self.broadcast = broadcast
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if broadcast:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._handlers: list[Callable[[bytes], None]] = []
        self._thread: threading.Thread | None = None
        self._running = False
        self._bound = False

    def bind(self) -> None:
        if not self._bound:
            self._sock.bind((self.host, self.port))
            self._bound = True

    def send(self, msg: bytes) -> None:
        if self.broadcast:
            addr = ("<broadcast>", self.port)
        else:
            addr = (self.host, self.port)
        self._sock.sendto(msg, addr)

    def receive(self) -> bytes:
        self.bind()
        data, _ = self._sock.recvfrom(65535)
        return data

    def subscribe(self, handler: Callable[[bytes], None]) -> None:
        self._handlers.append(handler)
        if self._thread is None or not self._thread.is_alive():
            self._running = True
            self.bind()
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()

    def _listen(self) -> None:
        while self._running:
            try:
                self._sock.settimeout(1.0)
                data, _ = self._sock.recvfrom(65535)
                for h in self._handlers:
                    h(data)
            except socket.timeout:
                continue
            except OSError:
                break

    def close(self) -> None:
        self._running = False
        self._sock.close()
