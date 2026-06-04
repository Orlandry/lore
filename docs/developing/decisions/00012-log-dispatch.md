---
status: accepted
date: 2025-11-20
deciders: Mattias Jansson
consulted: Raghav Narula, Valentin Ritzi
---

# ADR-00012: Log dispatch in core library

## Context and Problem Statement

We need a scalable way to dispatch log messages from the core library to the API caller both in
local in-process parallel execution and over IPC for service process execution.

## Decision Drivers

- Handle parallel execution with multiple parallel callers (in-process and IPC delivery)
- Added dependencies
- Execution overhead

## Considered Options

- Using tracing crate
- Using structured event dispatch

## Decision Outcome

Chosen option: Using structured event dispatch

Structured event dispatch can handle routing to the correct caller when executing in a service process

### Consequences

- Good, because we get the same log messages in all Lore-based applications when executing in-process and over IPC
- Good, because overhead is low
- Good, because there are no additional dependencies
- Bad, because it requires an extra glue function to pipe log messages to tracing

## Pros and Cons of the Options

### Using tracing crate

Log events and messages are generated using the standard `debug!`/`warn!`/`error!` macros and using the tracing crate
to deliver to the application tracing subscriber. Since there can be only one global subscriber, it means all
log messages go to the same subscriber for all Lore API calls.

In a model where the API call is executed in a service process it means that log messages will only be able to
be delivered within the service process and not routed to the correct caller pipe/socket for delivery in the
caller application. This means that application will get different results depending on if the call is executed
in-process or over IPC in a service process - a decision that's opaque to the caller.

Also, multiple parallel calls within an in-process execution model will get all log messages delivered to a single
subscriber (or callback) and not delivered to the per-call defined callback.

It also means that in a Rust application, the tracing subscriber will be put in the application code, and the
application is responsible for logging to a file or other serialization (possibly with library helpers).

- Good, because tracing is a standard mechanism and crate in Rust
- Good, because delivery overhead is low
- Bad, because a global subscriber means calls executed in a service process won't route log messages to the caller
- Bad, because enabling tracing in the core library has memory impact by increasing future sizes

### Using structured event dispatch

Log events and messages are delivered as structured events through the same channel as other library structured
events. This means we must use our own custom `urc_debug!` style log macros, turn them into structured events and
dispatch to the application through the callback supplied to each API call.

Log events and structured events are thus delivered over the same mechanism and in order, and each API call gets the
log events only for that specific call, irrespective of in-process execution or execution in a service process
over IPC.

Server can and will still use tracing for observability. Log events are routed to tracing with a small helper
function in the core library event dispatcher. Other applications can opt to use tracing for Lore logs by using
the same helper function glue.

- Good, because we get the same log messages in all Lore-based applications when executing in-process and over IPC
- Good, because overhead is low
- Good, because there are no additional dependencies
- Bad, because it requires an extra glue function to pipe log messages to tracing
