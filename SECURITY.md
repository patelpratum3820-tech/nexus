# Security Policy

## Threat Model & Security Posture

NEXUS is designed as an isolated, local-first desktop application. Its operational perimeter is confined to the local loopback interface (`127.0.0.1`).

### Core Security Guarantees

1. **Loopback Binding**:
   - The FastAPI backend binds exclusively to `127.0.0.1:8000`.
   - The Ollama interface communicates exclusively across `127.0.0.1:11434`.
   - No public network interfaces or remote endpoints are opened or accepted.

2. **Zero Remote Telemetry**:
   - NEXUS transmits no user queries, embeddings, or prompts to external cloud servers.
   - All inference operates entirely on local hardware.

3. **Process Integrity**:
   - NEXUS manages only its explicitly spawned child processes.
   - External system services and independently launched background applications are strictly protected from termination or signal manipulation.

## Reporting a Vulnerability

If you identify a security issue or boundary violation:
- Please open a private GitHub advisory or contact the project maintainer directly.
- Include reproduction steps and environment details.
