---
status: accepted
date: 2026-03-21
deciders: Mattias Jansson
consulted: Raghav Narula, Valentin Ritzi, Joshua Cohen
---

# ADR-00015: Log macro separation into lore-log crate with callback dispatch

Extends [ADR-00012: Log dispatch in core library](00012-log-dispatch.md).

## Context and Problem Statement

ADR-00012 established that log messages are delivered as structured events through per-call event dispatch,
using custom `urc_debug!` style macros in the core library. This works well for routing log messages to the
correct caller in both in-process and IPC execution models.

However, the log macros and log level types are defined in `lore-core`, with tight coupling to the execution
context and event dispatcher. This prevents other `lore-*` crates from using the same logging infrastructure
without depending on `lore-core`. Additionally, the server had a separate `LogTracer` trait bolted onto the
event dispatcher to bridge log events to tracing, creating two parallel delivery paths for the same log data.

We need to separate the log macro infrastructure from the core library so it can be reused across the
codebase, while preserving the per-call event dispatch behavior for client applications and the tracing
bridge for the server.

## Decision Drivers

- Log macros should be usable from any crate without depending on lore-core
- Per-call event dispatch must be preserved for correct IPC and parallel execution behavior (ADR-00012)
- Server must be able to route log messages to tracing for observability
- Client file logging shouldn't require a separate global event handler
- Single delivery path per consumer, not multiple parallel mechanisms

## Considered Options

- Keep macros in lore-core with a trait-based log sink
- Extract macros into lore-log with a single global callback
- Extract macros into lore-log with a subscriber/listener pattern

## Decision Outcome

Chosen option: "Extract macros into lore-log with a single global callback," because it provides the
simplest separation with a single configurable delivery path per application, and each consumer can set
the callback appropriate for its execution model.

### Consequences

- Good, because log macros and log level types are reusable from any crate via lore-log
- Good, because each application has a single log delivery path with no parallel mechanisms
- Good, because the lore interface crate callback handles both file logging and event dispatch in one place
- Good, because the server callback routes directly to tracing without intermediate event dispatch overhead
- Good, because the old LogTracer trait and dual-path delivery in the event dispatcher are eliminated
- Neutral, because lore-log has a global callback, so only one consumer can own log delivery at a time

## Pros and Cons of the Options

### Keep macros in lore-core with a trait-based log sink

The existing approach from ADR-00012. Log macros live in lore-core and directly access the execution context
to dispatch log events. A `LogTracer` trait on the event dispatcher provides a secondary path for the server
to bridge to tracing.

- Good, because it already works and is well understood
- Good, because per-call routing is handled directly in the macro expansion
- Bad, because other lore-* crates can't use the log macros without depending on lore-core
- Bad, because the LogTracer creates a second parallel delivery path alongside event dispatch
- Bad, because file logging in the client required either a LogTracer implementation or a global event handler

### Extract macros into lore-log with a single global callback

Log macros and the `LoreLogLevel` type move to a standalone `lore-log` crate with no dependencies on lore-core.
The macros check a global log level and call a single registered callback function. Each application sets the
callback appropriate for its needs:

- The lore interface crate sets a callback that writes to the log file (if configured) and dispatches through
  the execution context event dispatcher for per-call delivery
- The server overrides the callback to route directly to tracing macros with correlation ID from the
  execution context

- Good, because lore-log is a minimal crate usable from anywhere
- Good, because each application has exactly one log delivery path
- Good, because file logging and event dispatch are combined in a single callback, eliminating the need
  for a separate global event handler
- Good, because the LogTracer trait and dual-path delivery are eliminated entirely
- Neutral, because the global callback means only one consumer owns delivery at a time (but this matches
  the single-process execution model)

### Extract macros into lore-log with a subscriber/listener pattern

Similar to the callback approach but using a list of subscribers that all receive log events, similar
to how tracing layers work.

- Good, because multiple consumers can independently process log events
- Good, because lore-log is reusable from anywhere
- Bad, because multiple subscribers reintroduce the parallel delivery problem from the LogTracer approach
- Bad, because subscriber ordering and lifecycle management adds complexity
- Bad, because it's unclear which subscriber is responsible for per-call event dispatch

## More Information

The architecture after this decision:

```text
lore-log crate:
  LoreLogLevel enum, lore_trace!/lore_debug!/... macros
  Global callback + level filter

lore-core crate:
  UrcLogLevel = LoreLogLevel (type alias)
  urc_trace!/urc_debug!/... macros (forward to lore_ macros)
  Re-exports lore_log for macro hygiene

lore interface crate (log::initialize):
  Sets callback → write to log file + dispatch through execution context

lore-server (server_main):
  Overrides callback → route to tracing macros with correlation ID
```

This architecture will be updated as Lore refactoring progresses.
