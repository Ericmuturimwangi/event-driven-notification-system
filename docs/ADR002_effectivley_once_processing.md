# ADR-002: How "Exactly-Once" Processing Is (Not) Guaranteed

Status: Accepted Date: Phase 4 Deciders: Project owner + architecture review.
Related: ADR-001 (retry/idempotency sequencing)

## Context

The system must not send duplicate notifications and must not lose notifications.
True exactly-once delivery does not exist in distributed systems. This is not an implementation limitation of the project - it is a fundamental property of systems communicating over unreliable channels. Any system that claims exactly-once is actually implementing one of: - At-most-once(fire and forget): no duplicates, but messages are lost on any failure. Unacceptable - a lost "password reset" email is a support ticket. - At-least-once (retry until acknowledged): nothing is lost, but duplicated occur whenever an acknowledgement is lost after successful processing. The sender cannot distinguish "processing failed" from "processing succeeded but the ACK was lost"

--We pick at-least-once, then suppress duplicates at the consumer:
At-least-once delivery + idempotent consumers = Effectively once

Effectively once means: the side effect (one email in the user's inbox occurs once, even though message delivery and task execution may occur multiple times.
)

### Decision

- At-least-once delivery (the "never lose" half)
- Idempotent consumers (the "never duplicate" half)
- What is not guaranteed is the residual window
- Reason for not selecting alternatives:
  - At-most-once(acks_late=False, no retries): silent loss of notifications. Rejected - loss is worse than duplication.
  - Distributed transactions/ 3PC across DB + provider: SMTP and HTTP providers do not participate in two-phase commit. Not available
  - Kafka exactly-once semantics (EOS): Kafka EOS covers consumer-transform-produce within kafka. The moment the side effect leaves Kafka (an SMTP call), the same window reappers. Swapping brokers would not change the analysis, only the marketing./

### Mitigations available when this matters more

- shrink the window: commit the status update in the smallest possible transaction immediatley after the provider call (current implementation already does this.)

- Provider-level idempotency: pass event_id as the providers dedup token. The provider then suppresses the duplicate - this is the only mechanism that truly closes the window, by making the side effect itself idempotent.

- Transactional outbox / sent-ledge: write a "send attempted" record before calling the provider; ambingous states get reconciled against provider delivery logs rather than blindly re-sent.

### Consequences

#### Positive

- No notification is silently list: every failure path ends in COMPLETED, a scheduled retry, or a visible DLQ record.
- Duplicates from all three-system-internal sources are suppressed.
- The remaining duplicate risk is characterized, bounded, and has a named escalation path (provider-level idempotency) if requirements tighten.

#### Negative

- A duplicate notification is possible in the crash-between-send-and commit window.
- The status guard adds one SELECT per task execution. Negligible
- Operators must understand that an event in PROCESSING after a worker crasj is ambingupos (may or may not have been sent) and that replaying it may duplicate. The DLQ replay endpoint inherits this ambinguity.

#### Invariants future changes must preserve

- Event row is committed before the task is published
- visibility_timeout > longest retry countdown
- The status guard runs before any side effect.
- Status updates commit immediately after the side effect, in their own transaction.
