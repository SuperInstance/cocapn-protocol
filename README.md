# cocapn-protocol

Messaging protocol for the Cocapn Fleet — envelopes, bottles, messages, and deadband routing for inter-agent communication.

## What This Gives You

- **FleetMessage** — typed messages with sender, recipient, priority, and tracing
- **FleetEnvelope** — routing wrapper with hop count, return path, and SHA-256 checksums
- **Bottle** — message container for async fleet delivery
- **DeadbandRouter** — suppresses duplicate messages within a configurable deadband window

## Quick Start

```bash
pip install cocapn-protocol

from cocapn_protocol import FleetMessage, FleetEnvelope, Priority

msg = FleetMessage(
    sender="scout-alpha",
    recipient="keeper-beta",
    payload={"action": "report", "status": "nominal"},
    priority=Priority.NORMAL
)
envelope = FleetEnvelope(message=msg)
envelope.verify()  # Checks SHA-256 checksum integrity
```

## How It Fits

The communication layer for the Cocapn Fleet. Part of the SuperInstance ecosystem.

Related repos:
- [cocapn-identity](https://github.com/SuperInstance/cocapn-identity) — agent identity management
- [cocapn-core](https://github.com/SuperInstance/cocapn-core) — core fleet library
- [cocapn-telemetry](https://github.com/SuperInstance/cocapn-telemetry) — fleet observability

## License

Apache 2.0
