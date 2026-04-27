from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Bottle:
    """A message bottle with markdown serialization."""

    sender: str
    subject: str
    body: str
    priority: str = "P2"
    timestamp: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_markdown(self) -> str:
        """Serialize to markdown with frontmatter and sections."""
        ts = self.timestamp.isoformat() if self.timestamp else ""
        lines = [
            "---",
            f"sender: {self.sender}",
            f"date: {ts}",
            f"priority: {self.priority}",
            "---",
            "",
            f"# {self.subject}",
            "",
            "## Body",
            "",
            self.body,
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def parse_bottle(md_text: str) -> Bottle:
        """Parse markdown text back into a Bottle."""
        lines = md_text.splitlines()

        # Parse frontmatter
        frontmatter: dict[str, str] = {}
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].strip()
                if ":" in line:
                    key, val = line.split(":", 1)
                    frontmatter[key.strip()] = val.strip()
                idx += 1
            content_start = idx + 1
        else:
            content_start = 0

        sender = frontmatter.get("sender", "")
        priority = frontmatter.get("priority", "P2")
        date_str = frontmatter.get("date", "")
        timestamp: Optional[datetime] = None
        if date_str:
            try:
                timestamp = datetime.fromisoformat(date_str)
            except ValueError:
                timestamp = None

        # Parse subject and body from remaining markdown
        subject = ""
        body_lines: list[str] = []
        in_body = False
        for line in lines[content_start:]:
            stripped = line.strip()
            if stripped.startswith("# ") and not subject:
                subject = stripped[2:].strip()
                continue
            if stripped.lower() == "## body":
                in_body = True
                continue
            if in_body:
                body_lines.append(line)

        # Trim leading/trailing blank lines from body
        while body_lines and body_lines[0].strip() == "":
            body_lines.pop(0)
        while body_lines and body_lines[-1].strip() == "":
            body_lines.pop()

        body = "\n".join(body_lines)

        return Bottle(
            sender=sender,
            subject=subject,
            body=body,
            priority=priority,
            timestamp=timestamp,
        )
